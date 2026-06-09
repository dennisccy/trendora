# Goal Iteration 26 — Close the last buildable wave: capture J-37 / J-35 / J-39 defining flows + fix the J-38 Resume UX

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 26
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-37, J-38, J-39, J-35
- **Required-still-passing journeys:** J-08, J-15, J-17, J-18, J-33, J-34, J-36, J-06, J-07, J-01–J-05, J-09–J-14, J-16, J-19–J-21, J-25–J-32
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Import keys are env-or-session, never persisted.** The import provider catalog and each provider's key-requirement + env-var name MUST come from config (no hardcoded provider list in code); a provider key MUST be read from the environment, or — if the user pastes one into the import UI — held **in memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and never echoed back** in any response. The import's date inputs are **job parameters, not a second date control**.
  - **Pull-missing fetches exactly the gap, real-data-only, idempotently.** The one-click "pull the missing data" MUST construct a fetch covering **only** the diagnosed `(symbol, date)` shortfall and MUST run it through the existing chunked/checkpointed/resumable import path (no second fetch path); it MUST be **per-`(symbol, date)` idempotent (INSERT-new-only)** — re-fetching/duplicating nothing already stored, never overwriting a committed seed bar — and on provider failure it MUST surface an explicit error / rate-limited state and **fabricate no price** to clear a diagnostic row.
  - **Unfinished-imports actions are idempotent and audit-preserving.** Resume and Retry MUST re-fetch only outstanding work and produce **no duplicate fetch or row**; **Remove/Dismiss MUST drop only the actionable job-control record** — it MUST NOT delete, hide, mutate, or fabricate any **immutable scanner snapshot or forward-return row**, and the append-only `data_provider_runs` audit trail MUST remain the permanent record.
  - **Data removal is seed-safe & consistency-preserving.** Removal MUST target **only user-added bars**; the **committed seed MUST NEVER be deletable from the UI**, and a wholly-seed removal MUST be refused with an explicit reason. A **confirm-preview** MUST enumerate exactly what will be removed (bars + cascaded dependents) before anything is deleted. Deleting bars MUST **cascade-remove the snapshots and forward-returns derived solely from them** — a **whole-row deletion together with its provenance, NOT an in-place mutation/overwrite of a retained snapshot**.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(critical)*
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. *(critical — the recurring watch risk on `/data`)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*
  - **Single source of truth / No recompute in the read path / No magic numbers.** *(critical)*

## GOAL

Lift the last four buildable Data-Manager journeys from `partial` to `passing` by capturing each defining multi-step browser flow end-to-end against a deterministic, offline, browser-driveable source — and fix the one small J-38 Resume-without-key UX gap — so GOAL_ACHIEVED becomes reachable on the full buildable set (J-22/J-23/J-24 stay honestly NA / non-halting).

## BACKGROUND

J-37 (missing-data diagnostic + gap-exact pull), J-38 (unified Unfinished-imports), J-39 (seed-safe Remove-data), and J-35 (expand-universe) are all **BUILT, source-proven, and 601-tests-green** (coherence COHERENCE-PASS; J-37/J-38 already registered in the blueprint Data Contract). They sit at `partial` for one structural reason, confirmed across iters 23/24/25: their **defining multi-step flows were never captured in the browser** — the host carries no insufficient universe member (so the J-37 three-category diagnostic + pull never rendered), the only selectable import sources are live providers that are **Yahoo-429 / key-gated walled** (so a real J-37 pull / J-35 expand can never run to completion in the browser), and the dedicated browser-qa-agent repeatedly SKIPPED on a down/dead-shell frontend. The single new code enabler this iter is a **deterministic, env-gated, offline test import source** (the existing committed `SeedProvider`, exposed only when an env flag is set) plus a **QA fixture DB seeded with a no-history / thin / intra-series-gap member** — together these let the browser drive a real pull and a real expand to completion **without a live network**, satisfying the iter-4/15/23/24/25 multi-step-capture lesson. J-38 additionally needs a tiny UX fix (a needs-key Resume-without-key 400 must surface a VISIBLE inline error and not drop the row — the iter-25 dedicated-browser-qa FAIL on UT-11) and a captured SUCCESS Resume leg. J-39 needs only a re-capture via the non-destructive **preview** path (no code change). The prior evaluator recommended `full` depth; this touches backend (new test source + fixture wiring) + frontend (UX fix) + new tests, so `full` is correct.

**Lessons applied (episodic memory — surfaced for dev/reviewer/QA/evaluator):**
- *iter-25:* a needs-key Resume-without-key → 400 is a CORRECT spec error case, but exercising ONLY the error path leaves J-38's defining SUCCESS leg (continue from `next_chunk_index`) unverified → it must be `partial`. Capture a SUCCESSFUL Resume, not only the deliberate-error path. Byte-identical before/after shots (UT-11-before==UT-11-after) made the "row silently removed" narrative unreliable — trust the network log, capture **distinct sha256** before/after shots.
- *iter-23/24/25:* a control rendered in isolation (surface-presence) does NOT satisfy a multi-step acceptance; a host with no diagnostic-triggering data SKIPs the defining flow — **seed an injected fixture**, do not rely on a surface render.
- *iter-15 / MEMORY `browser-qa-dead-shell-next-cache` / `dev-server-cleanup-by-port`:* env-fix FIRST — stop strays **by port** (no broad `pkill`), `rm -rf apps/frontend/.next`, restart `next dev`, confirm `GET /_next/static/chunks/main-app.js` → 200 and the health badge clears BEFORE driving any UI; never run a prod `npm run build` against the live dev `.next`.
- *iter-21/22 / MEMORY `httpx-error-leaks-url-query-key`:* any NEW error string the pull/retry/resume surfaces is untrusted-for-secrets — assert the session key (and `?token=`/`?apikey=`) is ABSENT from `GET /api/data/jobs/{id}` + the job card via a REAL httpx-error path, not a sanitized mock.
- *MEMORY `j39-live-host-has-user-added-nvda-bars`:* the live host has user-added NVDA bars — the destructive J-39 confirm is proven by the **fixture**, NEVER run destructively on a real symbol live; the live capture uses the **preview** endpoint (deletes nothing).
- *MEMORY `react-controlled-select-needs-native-setter`:* Chrome MCP `select` does not fire React onChange on this frontend — use a native-setter + bubbling change event, then assert live DOM.
- *iter-10 / status.json:* `status.json` is written to the PHASE-namespace path `runs/goal-<sid>-iter-26/status.json`, not `runs/goal-session-<sid>/iter-26/` — check both before concluding an artifact is absent.

## IN SCOPE

### Backend
- [ ] **Deterministic offline test import source (the capture enabler).** Expose the existing committed `SeedProvider` (`apps/backend/app/data_providers/seed_provider.py`, already used as the default offline boot provider) as a **selectable import source named `seed`** in the `GET /api/data` `sources` payload **only when the env flag `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` is set** (off by default; never in the committed `config.yaml` `data_manager.providers` catalog, never available in production). When enabled, `compute_provider_availability` appends one entry `{id: "seed", label: "Seed (offline test data)", needs_key: false, supports_market_cap: true, available: true}`; `make_provider("seed", ...)` already resolves to `SeedProvider` (no change there). Route a pull/expand/fetch job whose `source == "seed"` through the **EXISTING J-34 chunked engine and the EXISTING `screen_reasons` predicate** — NO second fetch path, NO second screen rule. This is a test/dev affordance, not a production live provider — it serves **real committed seed bars** (not request-time-fabricated data), so *No fabricated data* and *Live fetch is real-data-only* are preserved.
- [ ] **J-37 / J-35 capture support is data, not code.** Do NOT change the diagnostic, the pull constructor, the expand screen, or the universe artifact writer — they are integration-proven. The browser capture runs against a **fixture DB** (below) over the `seed` source.
- [ ] **(QA-owned) Fixture DB for the capture.** Provide a reproducible fixture (a temp/throwaway DB the QA/browser harness boots, NOT the committed seed and NOT the live host DB) seeded so that: (a) one universe member has **no history at all**, (b) one has **thin history** below `indicators.min_history_bars`, (c) one has an **intra-series date gap**; and the `seed` source can supply the missing bars so a pull/expand runs to completion. (Implementation may be a small seed-builder script under `apps/backend` invoked by the QA harness; it MUST NOT mutate the committed `apps/backend/data/seed/` tree.)

### Frontend
- [ ] **J-38 Resume-without-key UX fix (the iter-25 UT-11 FAIL).** When a needs-key Resume is submitted without a key and the backend returns 400, the unfinished-imports row MUST remain visible and a VISIBLE inline `role="alert"` error MUST render on/near the Resume control (e.g. "Enter the session key for <label> to resume."). Verify the existing `ResumeControl` inline-error path (`apps/frontend/app/data/page.tsx:1275-1276,1321-1325`) actually renders on the 400, and ensure NO overview reload (`onResumed` / `loadOverview`) silently removes the row on a *failed* resume — `onResumed` already fires only on success (`page.tsx:178-184,1267-1280`); confirm and, if a reload path can drop the row, gate it so a failed resume never reloads the list. This is a small, surgical change — no new state, no new component.
- [ ] No other frontend change is required for J-37 / J-39 / J-35 — they are already built; this iter only captures their flows.

### New user-facing capability
Nothing newly user-facing in production. The four target journeys' capabilities already exist on `/data`; this iteration makes their defining flows **demonstrable** (via a deterministic offline source in the test/QA harness) and fixes one error-feedback gap on the J-38 Resume control.

### New information displayed
None new in production. In the QA harness only, the `seed` import source appears in the source picker (env-gated).

### New user actions
None new. The J-38 Resume control gains a visible error message on a needs-key-without-key failure (existing button, clearer feedback).

### UI surface changes
`/data` (Data Manager) only — the J-38 Resume control's failed-state feedback. No new pages, panels, routes, or nav entries.

### Product surface delta
The product experience is unchanged in production except that a Resume attempted without the required session key now shows a clear inline error instead of appearing to do nothing. The substantive delta is **verification coverage**: the four import/coverage journeys are now provable end-to-end offline.

### Blueprint conformance
All work homes on the **EXISTING approved `/data` (Data Manager)** page (sidebar, 1 click) — additive only, **no new page/route/nav entry, no nav-skeleton change, no `blueprint.reapproval-requested`**. J-37 and J-38 are already registered in the Data Contract (rows added iter-25, lines ~218/220). The `seed` test import source is a **test/dev harness affordance**, not a new displayed canonical value, and routes through the already-registered J-34 engine + `screen_reasons` predicate — it introduces no second computation or serving path for any contract value.

### Data-contract additions
None. No new displayed canonical value is introduced. The `seed` source serves committed bars through the existing canonical fetch path (`POST /api/data/jobs` → `start_data_job` → J-34 engine) and the existing universe-screen predicate (`screen_reasons`); the pull still reads the single `compute_coverage` diagnostic and the expand still writes the single canonical `universe.json` artifact. (A one-line note that the `seed` source exists as an env-gated test affordance may be added to the blueprint's `/data` section, but no Data-Contract value row is added.)

## OUT OF SCOPE

- **J-22 / J-23 / J-24** — externally Yahoo-429 data-walled, **NON-HALTING / NON-VETOING** per `docs/goal.md` lines 989–1012. Do **NOT** autonomously re-probe a live provider. J-22 auto-unblocks only when an operator points the Data Manager at a reachable cap-capable source and runs Expand.
- Any change to the diagnostic computation, the pull-job constructor, the expand screen rule, the universe artifact writer, the J-39 removal/cascade logic, or the J-34 engine — all are integration-proven; this iter captures their flows, it does not rebuild them.
- Any live network fetch in the capture path — the captures run against the **deterministic offline `seed` source**.
- Any new page, route, sidebar entry, or second date control.
- Any change to scoring / scanner / regime / patterns / buckets / forward_testing / research / snapshot_serving, or the `/stocks` · `/backtest` · `/research` pages, or `asof-provider` — **no DB regen** (J-06/J-07/J-15 must stay byte-identical).
- Shipping the `seed` import source enabled in production (it stays off by default and absent from the committed catalog).

## DEFINITION OF DONE

- [ ] **J-37 passes via browser-qa-agent**: against the fixture, the diagnostic renders **all three categories** (no-history / thin / intra-series-gap) each with the exact shortfall + symbol; clicking **Pull the missing data** (and **Pull all missing**) constructs a job whose `symbols` + `[start, end]` **equal the diagnosed gap** (NOT the whole universe/window — assert via the network request body); the job runs to **completion** over the `seed` source; the diagnostic row **clears/shrinks** and the J-36 per-symbol coverage table reflects the new bars. The honest empty-state and the provider-failure (no-fabrication) paths remain green.
- [ ] **J-38 passes via browser-qa-agent**: a **SUCCESSFUL Resume** of a no-key/env-key/`seed`-source resumable checkpoint **continues from `next_chunk_index`** (assert the resumed job runs and progresses, surviving a restart); Retry / Dismiss-preserves-audit / key-reprompt / key-not-echoed remain green; and the **UT-11 fix is verified** — a needs-key Resume-without-key → 400 shows a **visible inline error** and the row **stays** in the panel (capture **distinct** before/after shots).
- [ ] **J-39 passes via browser-qa-agent**: the Remove-data **confirm-preview** renders removable bars + range + the **protected committed-seed breakdown** ("committed seed" reason) + the dependent cascade; a **wholly-seed scope is refused** with an explicit reason. Use the **preview** endpoint on the live host (deletes nothing); the destructive confirm + cascade is captured against the **fixture** (never destructive on a real live symbol).
- [ ] **J-35 passes via browser-qa-agent**: an **injected/`seed`-source expand** runs end-to-end → **passers + omitted-with-reason** list + a **grown universe-count**, with `/methodology` size matching. (Live market-cap expansion over a walled provider stays NA / non-halting.)
- [ ] Required-still-passing journeys remain green — especially **J-18** (exactly one date `<select>` on `/data`; the new error feedback and `seed` source add **no date state**), **J-33** (key-leak scrub holds on any new pull/retry/resume error string — REAL-httpx assertion), **J-08** (J-38 Remove/Dismiss touches no snapshot/forward-return/audit row), **J-34** (Resume/Retry/pull reuse the engine — no fork), **J-36** (diagnostic reuses the single `compute_coverage` producer), **J-06/J-07/J-15** (scoring/snapshot path git-untouched, no DB regen).
- [ ] No anti-goal violation introduced. Both historical minor violations stay RESOLVED.
- [ ] Unit/integration tests pass; **no regressions** (full backend suite green; if a `table=True` model is added — none expected — update `tests/test_db.py:37` in the SAME change per the iter-22 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-26-dev.md`, stating honestly whether the live-provider paths (J-22-style) were exercised (they were not — data-walled, non-halting) and that the captures ran against the deterministic `seed` source + fixture DB.

## TESTING REQUIREMENTS

- **Browser (the heart of this iteration — capture the DEFINING multi-step flow for each, distinct sha256 shots):**
  - **J-37:** three-category diagnostic with exact shortfalls → gap-exact pull (assert request body `symbols`+`[start,end]` == diagnosed gap, not whole universe) → run to completion over `seed` → row clears + J-36 coverage updates → honest empty-state → provider-failure no-fabrication.
  - **J-38:** SUCCESSFUL Resume continuing from `next_chunk_index` (the never-captured success leg); needs-key Resume-without-key → 400 shows a visible inline error AND the row stays (the UT-11 fix); Retry, Dismiss-preserves-audit (Run history unchanged), key re-prompt, key-not-echoed (sentinel only as `type=password` value, 0× in job card / unfinished panel).
  - **J-39:** confirm-preview (removable bars + range + protected-seed breakdown + cascade) via the **preview** path on the live host; destructive confirm + consistency cascade + seed-only refusal against the **fixture** (never destructive on a live real symbol).
  - **J-35:** `seed`-source expand end-to-end → passers + omitted-with-reason → grown universe-count → `/methodology` size matches.
  - **J-18 (watch risk):** DOM-assert exactly one date `<select>` (the global as-of) on `/data`; zero date inputs added by the J-38 fix or the `seed` source.
  - **Env-fix gate BEFORE any UI:** stop strays by port, `rm -rf apps/frontend/.next`, restart `next dev`, confirm `GET /_next/static/chunks/main-app.js` → 200 + health badge cleared; serialize Chrome access (no concurrent qa + browser-qa on the shared tab — iter-6 lesson).
- **Unit/integration:**
  - The `seed` import source is exposed in `compute_provider_availability` **only** when `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` is set, and **absent** otherwise (assert both); a `source == "seed"` job dispatches through `start_data_job` / the J-34 engine and the `screen_reasons` predicate (no second path).
  - A REAL-httpx key-leak regression through the J-37 pull / J-38 retry/resume job-status surface still asserts the sentinel + `?token=`/`?apikey=` are ABSENT (re-run the iter-22/25 regression; confirm the `seed` source carries no key and leaks nothing).
  - The pull constructor produces `symbols`+`[start,end]` exactly equal to the diagnosed shortfall and is per-`(symbol,date)` idempotent (INSERT-new-only) — re-running stores no duplicate bar.
  - The fixture builder writes only to a throwaway/temp DB and never mutates `apps/backend/data/seed/`.
- **Error cases:**
  - Needs-key Resume without a key → 400 with a clear message; the frontend renders the inline error and keeps the row.
  - Pull over an unreachable provider → explicit error / rate-limited, **no fabricated bar** to clear a diagnostic row.
  - Expand over a `supports_market_cap: false` source → disabled/400 with reason (unchanged gate).
  - Wholly-seed Remove scope → refused with an explicit reason (no silent partial).

## NOTES

- **This is the last buildable wave.** After these four capture green and nothing regresses, the buildable set is complete and **GOAL_ACHIEVED is reachable** — with J-22/J-23/J-24 (and the *live* outcomes of J-35 expand / J-37 pull / J-38 retry over a real walled provider) recorded honestly as **NA / non-halting / non-vetoing** per `docs/goal.md` lines 989–1012. Do **NOT** declare completion on a single import-journey landing (the iter-20 re-scope trap) — all four targets must capture green.
- **Why a new (small) backend change rather than a pure re-capture:** iters 23/24/25 proved that a pure re-capture cannot succeed — the host has no insufficient member and the only selectable sources are live-walled, so the defining J-37 pull / J-35 expand flows can never run to completion in the browser. The env-gated deterministic `seed` source + a fixture DB is the minimal, anti-goal-safe enabler that turns these from forever-`partial` into demonstrable-`passing`. It is OFF by default and never enters the production catalog, so production behavior (live-only, real-data-only) is unchanged.
- **Evidence hygiene:** sha256-dedupe all shots; the iter-25 collisions (UT-11-before==UT-11-after; several sharing one sha) must not recur. Each before/after claim rests on **distinct** shots + a DOM/network assertion.
- **Status/artifact note:** `status.json` lands at the PHASE-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-26/status.json`; full-depth iters in this session historically ship no `-audit.md` handoff and may leave `runs/goal-session-.../iter-26/` holding only `coherence.md` + `snapshot-sha`. The evaluator should verify critical seams in source and trust the dedicated `ui-test-results.md` over the QA MODE-2 surface table.
- **Coherence:** iter-25 was COHERENCE-PASS; no consolidation pass is forced. One advisory carry-over (non-blocking): the legacy `resumable_imports` array is still served alongside `unfinished_imports` for backward compatibility (frontend renders only the new one — no data shown twice); a future iter MAY deprecate it. Do not action it here unless it surfaces a duplicate in the browser.
