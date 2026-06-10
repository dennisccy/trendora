# Goal Iteration 27 — Capture the four carried-partial Data-Manager flows end-to-end against the fixture DB

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 27
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-37, J-38, J-39, J-35
- **Required-still-passing journeys:** J-17, J-18, J-33, J-34, J-36, J-08, J-06, J-07, J-15
- **Anti-goal reminders:**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. The Stock-Detail chart **timeframe selector** (1D/1h/15m/5m) is NOT a date control — it changes bar granularity only, bounded by the resolved as-of date. The Research **all-history / as-of-date** toggle is likewise a MODE, NOT a date control — its as-of mode reads the same single global as-of control (no second date state). *(extends Single source of truth)*
  - **Import keys are env-or-session, never persisted.** ... a provider key MUST be read from the environment, or — if the user pastes one into the import UI — held **in memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and never echoed back** in any response. The import's date inputs are **job parameters, not a second date control**. *(extends Live fetch is real-data-only + Exactly one date selector)*
  - **Pull-missing fetches exactly the gap, real-data-only, idempotently.** The one-click "pull the missing data" MUST construct a fetch covering **only** the diagnosed `(symbol, date)` shortfall and MUST run it through the existing chunked/checkpointed/resumable import path (no second fetch path); it MUST be **per-`(symbol, date)` idempotent (INSERT-new-only)** ... on provider failure it MUST surface an explicit error / rate-limited state and **fabricate no price** to clear a diagnostic row.
  - **Unfinished-imports actions are idempotent and audit-preserving.** Resume and Retry MUST re-fetch only outstanding work ...; **Remove/Dismiss MUST drop only the actionable job-control record** — it MUST NOT delete, hide, mutate, or fabricate any **immutable scanner snapshot or forward-return row**, and the append-only `data_provider_runs` audit trail MUST remain the permanent record.
  - **Data removal is seed-safe & consistency-preserving.** Removal MUST target **only user-added bars** — the **committed seed MUST NEVER be deletable from the UI**, and a wholly-seed removal MUST be refused with an explicit reason. A **confirm-preview** MUST enumerate exactly what will be removed (bars + cascaded dependents) before anything is deleted. Deleting bars MUST **cascade-remove the snapshots and forward-returns derived solely from them** — a **whole-row deletion ... NOT an in-place mutation/overwrite of a retained snapshot**. Removal MUST **fabricate nothing**.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. (The `seed` import source serves REAL committed seed bars — not request-time-fabricated data.)
  - **Snapshots are immutable / No recompute in the read path.** No DB regen; the scoring/snapshot compute path MUST stay untouched so J-06/J-07/J-15 are byte-identical.

## GOAL

Prove the four remaining Data-Manager Must-haves end-to-end in the browser — by booting the QA/browser harness against the deterministic fixture DB + the env-gated offline `seed` import source so each defining multi-step flow (missing-data diagnostic → gap-exact pull, successful Resume-from-checkpoint + the needs-key error fix, seed-safe Remove confirm-preview, seed-source expand to grown universe) actually runs to completion and is captured — turning J-35/J-37/J-38/J-39 from `partial` to `passing`.

## BACKGROUND

The board is **32 passing / 4 partial (J-35, J-37, J-38, J-39) / 3 failing (J-22/J-23/J-24, externally data-walled, NON-HALTING / NON-VETOING)**. The four targets are `partial` for the **same single reason across iters 23/24/25/26**: their machinery is BUILT, source-verified, and covered by the 610-green suite, but their **defining browser flows were never captured** because the dedicated browser-qa-agent ran against the LIVE host with `TRENDORA_ENABLE_SEED_IMPORT_SOURCE` unset and no fixture DB booted — so the live universe had no insufficient member (diagnostic showed its honest empty-state), no resumable checkpoint existed (ResumeControl never rendered), and the `seed` source never appeared in the picker. **This is a capture / harness-wiring gap, not a code gap.** The iter-26 enabler — the env-gated offline `seed` import source (`data_manager.py:_seed_import_entry`, off by default), the fixture builder `apps/backend/scripts/build_qa_fixture_db.py` (prints the three env values as a JSON line), and the J-38 ResumeControl visible-inline-error fix (`data/page.tsx:1332` `role="alert" data-testid="resume-error"`) — is **committed at HEAD `77d0816`** (`git diff --stat HEAD -- apps/ config.yaml` is empty). The iter-26 evaluator's explicit iter-27 recommendation is **capture-only**. Full depth: four target journeys, the principal anti-goal watch surfaces (key-leak scrub on new error strings, exactly-one-date-selector, seed-safe cascade), and a real harness-wiring + screenshot-hygiene discipline that has failed four times running.

**Lessons being applied (surface to dev/QA/evaluator):**
- *iter-4/15/23/24/25 multi-step-capture lesson:* a render of surfaces in isolation, a blank/byte-identical frame, or exercising only the deliberate-error path does NOT satisfy a multi-step defining flow even when the logic is source- and test-proven. Each target's DEFINING flow must be captured with **distinct, hydrated, sha256-deduped** screenshots.
- *MEMORY `browser-qa-dead-shell-next-cache` + `dev-server-cleanup-by-port`:* env-fix FIRST — stop strays **by port** (never broad `pkill -f "next dev"`/"uvicorn"), `rm -rf apps/frontend/.next`, confirm `_next/static/chunks/main-app.js` 200 + the "Checking backend…" health badge cleared BEFORE driving any UI; a dead-shell SKIP is environmental, not a code FAIL.
- *MEMORY `j39-live-host-has-user-added-nvda-bars`:* the live host is NOT user-bar-free (NVDA has 6 bars beyond seed; a live destructive remove would cascade ~5 snapshots and `trendora.db` is gitignored/unrestorable). Drive J-39 via the **non-destructive PREVIEW endpoint** on the live host; the destructive confirm + cascade is proven ONLY against the throwaway fixture DB, NEVER on a real live symbol.
- *MEMORY `httpx-error-leaks-url-query-key`:* grep the **job-status response** (`GET /api/data/jobs/{id}` `errors[]`) and the job card, not just `/api/data`/DB, when asserting no key leak on any new pull/retry/resume error string.
- *iter-3/6 process gap:* full-depth iters in this session finish without an `-audit.md`; `status.json` lands at the PHASE-namespace path `runs/goal-<iter-name>/status.json`. De-dup evidence by sha256; ground every before/after claim on distinct shots + a DOM/network assertion.

## IN SCOPE

### Backend
- [ ] **No production backend code change.** The build is committed at HEAD. The ONLY backend activity is **harness wiring**: run `apps/backend/scripts/build_qa_fixture_db.py` to produce the throwaway fixture DB + narrowed config + seed overlay, and **boot the backend with the three env values it prints** (`TRENDORA_ENABLE_SEED_IMPORT_SOURCE=1`, `TRENDORA_CONFIG=<out>/config.yaml`, `TRENDORA_SEED_IMPORT_DIR=<out>/seed_overlay`). The fixture seeds a no-history / thin / intra-series-gap member so the three diagnostic categories render with exact shortfalls, and a `market_caps.csv` overlay so a `seed` expand can screen.
- [ ] If — and ONLY if — capturing a target surfaces a genuine code defect (e.g. the gap-exact pull job scope is wider than the diagnosed shortfall, a successful Resume does not continue from `next_chunk_index`, or a new error string leaks a key), apply the minimal fix on the canonical path (the existing J-34 engine / `screen_reasons` predicate / redacted-URL+scrub) and add a regression test. Do NOT fork a second fetch/screen/compute path. Otherwise this iteration writes no backend source.

### Frontend (if applicable)
- [ ] **No production frontend code change expected.** The J-38 ResumeControl visible-inline-error fix (`data-testid="resume-error"`, `role="alert"`) is already at HEAD. Only apply a minimal frontend fix if a capture exposes a real UX defect on a target flow (e.g. a failed Resume still silently drops the row, or the gap-exact pull / expand result panel does not render its passers/omitted/grown-count). Confine any such fix to the existing `/data` `page.tsx` components; add no new date state, no new page/route/nav entry.

### New user-facing capability
No NEW capability — this iteration converts already-built capabilities from `partial` to `passing` by demonstrating them end-to-end: a user can (J-37) see exactly which universe members are no-history / thin / intra-series-gap and one-click pull exactly the missing `(symbol,date)` gap to completion so the row clears and coverage updates; (J-38) Resume an unfinished import so it continues from the last completed chunk, and see a visible inline error (row retained) when a needs-key Resume has no key; (J-39) preview exactly what a Remove would delete (user-added bars + cascade, with the committed seed protected, a wholly-seed scope refused) before confirming; (J-35) run an Expand-universe job that produces passers + omitted-with-reason and a grown universe count matching `/methodology`.

### New information displayed
None new. The capture demonstrates already-registered values rendering against fixture data: the J-37 three-category diagnostic with exact shortfalls; the J-38 Unfinished-imports list with a real resumable checkpoint + Resume success state; the J-39 confirm-preview breakdown (removable vs protected-seed); the J-35 expand result (passers / omitted-with-reason / grown universe count).

### New user actions
None new. Exercised: "Pull the missing data" / "Pull all missing" (J-37); Resume / Retry / Remove-Dismiss (J-38); Remove-data Preview → confirm (J-39, confirm only against the fixture DB); select the `seed` source → start Expand (J-35).

### UI surface changes
None — all four flows live on the EXISTING `/data` (Data Manager) page (the Coverage panel + Missing-data diagnostic, the Unfinished-imports panel, the Remove-data form, the Import source picker + expand controls).

### Product surface delta
No structural delta. The product experience is unchanged from iter-26 in production (the `seed` source is OFF by default and never in the committed `config.yaml` catalog); the change is that the four Data-Manager flows are now demonstrably end-to-end and recorded as `passing` rather than `partial`.

### Blueprint conformance
No new surfaces. All four targets home on the EXISTING approved **`/data` (Data Manager)** page under the persistent sidebar (Information Architecture, `blueprint.md`). **No nav-skeleton change, no `blueprint.reapproval-requested` marker is written** (confirmed ABSENT).

### Data-contract additions
**None.** J-36/J-37/J-38 values were registered at iters 24–25; J-35 universe value and J-39 removal preview/cascade at iters 23–24. This iteration introduces no new displayed value — it reads existing canonical producers/endpoints: J-37 diagnostic + pull via `compute_coverage` + the J-34 engine; J-38 via `import_checkpoints` / `DataProviderRun` + the J-34 resume endpoint; J-39 via the `data_manager` remove preview/cascade; J-35 via the existing `expand` job kind + `screen_reasons` + the canonical `universe.json` (read by `/api/methodology` size + `/api/data` `universe_count`). **Never introduce a second computation/endpoint for any of these — read the registered canonical source.**

## OUT OF SCOPE

- Any production code change to the scoring/scanner/regime/patterns/buckets/forward_testing/research/snapshot_serving engines or the `/stocks`·`/backtest`·`/research` pages or the as-of provider/sidebar (a `git status` over these MUST stay EMPTY → no DB regen).
- Re-probing J-22 / J-23 / J-24 (externally Yahoo-429 data-walled, NON-HALTING / NON-VETOING per `docs/goal.md` 994–1012). Do NOT autonomously retry a live bulk/intraday/market-cap fetch. The `seed`-source captures are OFFLINE against committed bars and are NOT a J-22/23/24 live re-probe.
- Any NEW page, route, nav entry, endpoint, or Data-Contract value.
- Committing the `seed` source into the production `config.yaml` catalog, or enabling it by default — it stays env-gated and OFF in production.
- Running the destructive J-39 confirm against any real live symbol — destructive confirm + cascade is proven ONLY against the throwaway fixture DB; the live host uses the non-destructive PREVIEW path only.

## DEFINITION OF DONE

- [ ] **J-37** passes via browser-qa-agent: against the fixture DB, the three diagnostic categories (no-history / thin / intra-series-gap) render with exact shortfalls; a gap-exact pull over the `seed` source runs to completion with the job's `symbols + [start,end]` == the diagnosed gap (NOT the whole universe/window) → the diagnostic row clears and J-36 coverage updates.
- [ ] **J-38** passes via browser-qa-agent: a SEEDED resumable `seed`-source checkpoint is Resumed SUCCESSFULLY continuing from `next_chunk_index` (distinct before/after sha) AND the UT-11 fix is shown (needs-key Resume-without-key → backend 400 → visible inline `resume-error` alert → the row stays).
- [ ] **J-39** passes via browser-qa-agent: the Remove-data confirm-preview enumerates removable user-added bars + range + protected committed-seed breakdown + dependent cascade (PREVIEW path on the live host); a wholly-seed scope is refused with an explicit reason; the destructive confirm + whole-row cascade (no in-place overwrite) is demonstrated ONLY against the fixture DB.
- [ ] **J-35** passes via browser-qa-agent: a `seed`-source Expand runs end-to-end → passers + omitted-with-reason list → grown universe count, with `/methodology` resolved size matching `/api/data` `universe_count`.
- [ ] Required-still-passing journeys remain green: J-17, J-18 (THE flagged watch risk — exactly one global as-of `<select>` per page; the seed source / expand / pull / resume controls add ZERO new date state), J-33 (key-leak scrub HELD on every new pull/retry/resume error string — REAL-httpx assertion + grep the job-status response/job card), J-34, J-36, J-08 (Dismiss/Remove drops only job-control; audit + immutable rows preserved), J-06/J-07/J-15 (scoring/snapshot path git-untouched, no DB regen, byte-identical).
- [ ] No anti-goal violation introduced (the five restated above are the live risks).
- [ ] Unit tests pass; no regressions (the existing 610-green suite stays green; run pytest ONCE per MEMORY `backend-test-suite-runtime` — full suite ~14 min, never two concurrent invocations). If `tests/test_db.py:37` ever needs a table added, do it in the same change (iter-22 lesson) — but no new table is expected.
- [ ] Evidence is sha256-deduped — NO blank/dark or byte-identical before/after frames (the iter-25/26 hygiene blemish must not recur); every before/after claim rests on distinct hydrated shots + a DOM/network assertion.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-27-dev.md` — it MUST print the exact fixture-build + env-export + clean-boot recipe (build_qa_fixture_db.py → its three printed env values → stop-by-port + `rm -rf .next` + main-app.js 200 + health badge cleared) so the QA/browser step wires to the fixture, not the live host.

## TESTING REQUIREMENTS

- **Environment FIRST (gates everything):** stop strays BY PORT (backend :8835 region / frontend :3835 region — never broad `pkill`); `rm -rf apps/frontend/.next`; run `cd apps/backend && .venv/bin/python scripts/build_qa_fixture_db.py`; export the three env values from its final JSON line and (re)start the backend with them; confirm `_next/static/chunks/main-app.js` 200 and the "Checking backend…" health badge cleared before any UI capture. A dead-shell/down-server result is recorded SKIPPED (environmental), not FAIL — but with the fixture correctly wired, the four flows MUST be reachable, so a SKIP here means re-wire, not accept.
- **Browser (by ID):** J-37 (three-category diagnostic + gap-exact pull-to-completion → row clears + coverage updates), J-38 (SUCCESSFUL Resume-from-checkpoint, distinct before/after sha + the needs-key Resume-without-key visible-error/row-retained fix), J-39 (confirm-preview removable+protected-seed breakdown + wholly-seed refusal via PREVIEW on live; destructive confirm+cascade on fixture only), J-35 (seed-source expand → passers + omitted-with-reason + grown universe count matching `/methodology`). Re-verify J-18 (DOM `querySelectorAll('select, input[type=date]')` — exactly one global as-of `<select>`; job/action date inputs are parameters) and J-17 (existing fetch/backfill/both path intact).
- **Unit/integration:** rely on the existing 610-green suite (offline `seed`-expand passers/omitted, gap-exact idempotent pull, resume-from-`next_chunk_index`, needs-key-Resume-400, seed-safe remove + wholly-seed refusal, real-httpx key-leak scrub). Add a regression test ONLY if a capture surfaces a genuine defect; place it on the canonical path.
- **Error cases (must surface honestly, never fabricate):** a needs-key Resume with no key → backend 400 + visible inline `resume-error` (row retained, not silently dropped); a wholly-seed Remove scope → refused with explicit reason; a provider failure on pull/expand → explicit error / rate-limited state, no fabricated bar; any new pull/retry/resume/expand error string → key-scrubbed (sentinel + `?token=`/`?apikey=` absent from `GET /api/data/jobs/{id}`, the job card, and run history).

## NOTES

- This is the iter-26 evaluator's explicit **capture-only** iter-27 (the build is DONE and committed at HEAD `77d0816`; only browser-harness wiring to the fixture DB is missing). The decisive failure mode to avoid is the iter-23/24/25/26 recurrence: running the dedicated browser-qa-agent against the LIVE host with the seed env flags unset — then NO target flow is reachable and all four stay `partial`. The dev handoff MUST make the fixture-DB + three-env-value boot recipe impossible to miss, and the browser-qa-agent MUST drive the fixture, asserting the `seed` source is present in the picker BEFORE attempting an expand/pull.
- **Do NOT declare completion on a single import-journey landing (iter-20 re-scope trap):** the evaluator owns the verdict. GOAL_ACHIEVED becomes reachable only after all four targets capture green AND nothing regresses; J-22/J-23/J-24 (and the *live* outcomes of expand/pull/retry over a real walled provider) stay recorded honestly NA / non-halting per goal.md 994–1012 — they do NOT block GOAL_ACHIEVED.
- Process expectation (iters 2/3/6/9–26 pattern): likely no `-audit.md`; `status.json` at the PHASE-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-27/status.json`. The evaluator will substitute source + live verification and reconcile any QA-vs-dedicated-browser-qa divergence — so make the dedicated browser-qa run the authoritative, fixture-wired one this time.
- Coherence at iter-26 was COHERENCE-PASS (0 Part A / 0 Part B). This iteration introduces no new value or path, so coherence should stay PASS; no consolidation pass is owed.
