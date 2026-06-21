# Goal Iteration 43 — Live re-verification of J-100 + the byte-identity-protected rendered surfaces (no code rework)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 43
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-100
- **Required-still-passing journeys:** J-94, J-96, J-93, J-36, J-37, J-39, J-85, J-87, J-88, J-89, J-90, J-97, J-98, J-99, J-18 (CRITICAL), J-07 (CRITICAL), J-06
- **Anti-goal reminders:**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The relocated as-of-scoped evidence aggregate is likewise derived once per resolved as-of date, persisted/cached, and read from storage — never recomputed per request. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector.** No page-local or second date state; the single global as-of switcher is the only date control. *(critical — J-18)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens; any live-provider key is read only from the environment. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, cutoff, bucket edge, universe entry, and theme definition MUST come from config — no such literal in calculation code.
  - **Coverage & missing-data are descriptive & honest.** Coverage figures / the per-member table / the insufficient-for-analysis diagnostic MUST be read-only metadata derived from the stored bars + config — they MUST NOT recompute or restate any canonical score, return, bucket, or setup. *(extends No fabricated data + No recompute in the read path)*

## GOAL

Prove with live, rendered, evaluator-viewable evidence that the iter-42 J-100 bounded-resource backend hardening left every displayed value byte-identical to the pre-change baseline — so J-100 can flip to passing and the byte-identity-protected required surfaces are freshly re-verified — without changing a single line of source code.

## BACKGROUND

iter-42 built J-100 (the LAST unbuilt buildable Must-have: a single-flight + result cache around `compute_coverage`, a membership-specific dataset stamp decoupled from forward-return churn, a reused process-level bar cache, and config-sourced ops guards in `start-backend.sh`) — the code is correct and byte-identical at the compute layer (audit re-ran K=12 concurrent probes → 1 heavy compute, every payload deep-equals the single-request baseline), COHERENCE-PASS, review PASS, QA PASS, audit PASS_WITH_GAPS, closure passed. But it is held `failing` because the two standing GOAL_ACHIEVED closure conditions are not yet positively evidenced: (1) the FLUSHED full-suite `0 failed, EXIT 0` terminal line never appeared (the QA log stopped at 976 passed / 0 failed mid-`test_warmup.py`; the nohup suite was only ~17% at eval time — and the iter-11/29/37 lesson forbids blocking the evaluator on the in-flight suite), and (2) browser-QA was AUTO-SKIPPED (Frontend Present: no) so the protected RENDERED surfaces (J-94/J-96 on `/data`, J-93 on `/stocks`, the Dashboard cluster) have NO live render proof the optimization changed no served value. This iteration is the iter-36→37 / iter-39→40 backend-only-pair closing half (fourth repeat), prescribed verbatim by the iter-42 evaluator: a LEAN live re-verification with NO code rework. The working tree has no pending source diff (the iter-42 change is committed at HEAD `ca3d2b7`), so the developer step is a no-op and the value comes entirely from the live browser-QA pass plus confirming the flushed green suite. After this, the only non-green journeys are J-22/J-23/J-24, which are data-walled and NON-VETOING per goal.md:2445-2534 + the data-dependency notes — so this iteration's success makes the next evaluation a sound GOAL_ACHIEVED candidate.

## IN SCOPE

### Backend
- [ ] NONE — no backend code change. This is a verify-only live re-verification. (The iter-42 J-100 fix is already committed and correct; re-running dev MUST be a no-op.)

### Frontend (if applicable)
- [ ] NONE — no frontend code change. (`Frontend Present: yes` is set ONLY to force the browser-QA step to run live render capture — it is NOT a request to change frontend files. The iter-36/39/42 lesson: a backend-only `Frontend Present: no` iteration auto-skips browser-QA, which is exactly the failure that left J-100 unrenderable last iter.)

### New user-facing capability
None new. This iteration re-verifies that the user-facing surfaces still render the pre-iter-42 numbers under the hardened backend.

### New information displayed
None. Every value re-rendered this iteration is an EXISTING canonical value; the acceptance is that it is byte-identical to the pre-change baseline.

### New user actions
None.

### UI surface changes
None. The `/data`, `/stocks`, and Dashboard (`/`) surfaces are re-rendered as-is for verification only.

### Product surface delta
No change to the product experience by design — J-100's entire claim is "no served value changed; the VM no longer freezes under concurrent load." This iteration produces the live evidence that the claim holds at the render layer.

### Blueprint conformance
No new surfaces. All re-verified pages already have canonical homes in `blueprint.md`: `/data` (Data Manager — J-36/J-37/J-39/J-85/J-94/J-96/J-99), `/stocks` (J-93), Dashboard `/` (J-87/J-88/J-89/J-90/J-97/J-98). J-100 is the pre-registered backend-hardening annotation on the existing `compute_coverage` → `GET /api/data` canonical path (no new Data Contract row). Blueprint is unchanged this iteration.

### Data-contract additions
none. No new displayed value is introduced; no second computation or endpoint is added. The hardened `compute_coverage` remains the single canonical computing module for the coverage / membership-timeline / universe-diagnostic values it already serves via `GET /api/data` — read it from there; do not recompute.

## OUT OF SCOPE

- ANY source code change (backend or frontend). If the live re-verification surfaces a genuine NEW defect (not a stale screenshot / selector false-negative / environment flake), record it and stop — do NOT fix it in this lean verify-only iteration; the decomposer will scope a follow-up.
- Re-triggering the J-85 `kind:rebuild` snapshot regeneration (~11h, destructive, clears the snapshot layer) — the data is correct; never trigger it for QA.
- Concurrently probing `/api/data` (pool-exhaustion / freeze risk — MEMORY lesson). Load-test K parallel calls is the J-100 acceptance, but the human-facing verify pass SINGLE-loads `/api/data`.
- Building, queuing, or planning any new journey beyond J-22/J-23/J-24 — there are no remaining unbuilt buildable Must-haves (J-100 was the last; iter-22 lesson check confirmed against journey-history).
- Marking any journey passing on inference / API-layer byte-identity alone — a rendered journey requires live rendered pixels (iter-17/25/30/36/39/42 strict rule).

## DEFINITION OF DONE

- [ ] J-100 verified via browser-qa-agent: live, non-skeleton render evidence shows the `/data` coverage diagnostic + membership timeline, `/stocks`, and the Dashboard cluster all display numbers byte-identical to the pre-iter-42 baseline (the J-100 byte-identity property, observed at the render layer), AND the full-suite `0 failed, EXIT 0` line is confirmed flushed.
- [ ] Required-still-passing journeys (J-94, J-96, J-93, J-36, J-37, J-39, J-85, J-87, J-88, J-89, J-90, J-97, J-98, J-99, J-18, J-07, J-06) remain green on live evidence.
- [ ] CRITICAL invariants re-confirmed live: J-18 = 0 native `input[type=date]` on every re-verified page (exactly one date selector); J-07 = a Risk-Off as-of yields 0 Actionable; J-06 = the `/data` universe-resolution diagnostic admitted count reconciles with the served `/stocks` membership count (single source).
- [ ] No anti-goal violation introduced (trivially held — zero source diff this iteration).
- [ ] Full backend pytest suite flushes `0 failed, EXIT 0` (nohup-async via the pump; the evaluator is gated on the flushed terminal line, NEVER blocked on the in-flight stream — iter-11/29/37).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-43-dev.md` stating explicitly that NO code changed and the iteration is a live re-verification.

## TESTING REQUIREMENTS

- **Browser (the load-bearing gate this iteration):**
  - J-100 — the byte-identity property at the render layer: bring up `:8835` (WAIT for `GET /api/health` "ready"; warm-up precomputes the membership cache — a cold pre-warm `/api/data` still pays ~10-12s by design, so SINGLE-load it and be patient; NEVER concurrently probe it), `:3835`, `:9222`. Capture the `/data` coverage diagnostic + the rising membership-timeline step function (~2021-10-18 onward, populated Entries/Exits, the 3 honesty labels scrolled into the viewport) + `/stocks` slide + the Dashboard cluster, and confirm the rendered numbers match the pre-iter-42 baseline (e.g. the iter-37 `/api/data` stats `[544,548,122,585,1369,1370]` / iter-41 `/stocks` 544-of-544 / Dashboard Regime 73.44, Phase Expansion 28.75).
  - J-94 — `/data` universe-resolution diagnostic renders: admitted count + excluded-by-reason (below-history / below-price / below-ADV), all non-NaN.
  - J-96 — `/data` membership-timeline step function rises from ~2021-10-18 with populated Entries/Exits and all 3 honesty labels (reject any un-hydrated skeleton frame — iter-18/33 precedent).
  - J-93 — `/stocks` still slides per as-of (fast `/api/stocks` snapshot path; capture at least two ROW-COUNT-DISTINCT, BYTE-DISTINCT frames: an early honest-empty/small as-of vs a full ~544 as-of).
  - J-36 / J-37 / J-39 / J-85 — co-located `/data` surfaces render unchanged.
  - J-87 / J-88 / J-89 / J-90 / J-97 / J-98 / J-99 — Dashboard cluster renders unchanged (regime/phase card, market-phase chart bottom pane, at-a-glance summary + expand, membership-timeline pagination/filter).
  - J-18 (CRITICAL) — 0 native `input[type=date]` on `/data`, `/stocks`, and `/`.
  - J-07 (CRITICAL) — a Risk-Off as-of → 0 Actionable on the scanner run.
  - J-06 — `/data` diagnostic admitted count == served `/stocks` membership count (single-source reconciliation).
- **Unit/integration:** No new tests (no code change). The standing gate is the EXISTING full backend pytest suite flushing `0 failed, EXIT 0`. Split fast (no-boot) vs slow (`loaded_engine` seed-boot) tests if needed (iter-29 lesson); the targeted J-100 modules are `tests/test_data_manager_concurrency_load.py` (K parallel → 1 compute, byte-identical) and `tests/test_data_manager_membership_cache.py` (warm-up FR-insert HIT vs snapshot-add MISS).
- **Error cases:** None new to reject (verify-only). Honest-empty legs still apply: an early as-of must render an honest-empty `/stocks` (no fabricated rows) and the diagnostic must show NA for thin/insufficient members (no fabricated coverage).

## NOTES

- **Lesson — plan the Playwright fallback UP FRONT (iter-38/39/40/42).** The Chrome MCP CDP WebSocket timeout has emptied the evidence dir on iters 38, 39, and 40; the live evidence was captured ONLY on iters 34/37/40, and only because the browser-qa-agent planned the Playwright fallback before Chrome MCP timed out. Do NOT wait for Chrome MCP to fail first — a backend-correct, code-byte-unchanged fix still cannot flip J-100 to passing without live rendered evidence.
- **Lesson — md5sum the evidence dir FIRST (iter-10/15/18/33/40).** Reject any un-hydrated skeleton frame, any byte-identical "before/after" differential pair (the J-97 synced-zoom pair has silently been byte-identical across iters 38-40 — if J-93's two as-of frames or any differential pair share an md5, re-capture until they differ), and validate filename-vs-content for any shared-byte capture.
- **Lesson — NEVER concurrently probe `/api/data` in the human-facing verify pass (MEMORY pool-exhaustion).** `/api/data` is ~10-12s warm by design after the iter-37 known-limitation; the page fetches it once on load with no polling. The K-parallel concurrency assertion belongs to the J-100 load test, not the render pass.
- **Lesson — gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line (iter-11/29/37); NEVER block the evaluator on the in-flight suite.** Run the full suite nohup-async via the pump. Re-run any isolated `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` in ISOLATION before attributing it — these are the documented scanner_runs-race / slow-boot / warm-up-contention flakes on this 1369-run host (iter-30/34/36), `exit=137` in a background-helper log is the harness-kill, not a test failure (iter-29).
- **Lesson — cache-correctness must hit the LIVE current as-of, a cache HIT (iter-38).** When confirming the J-94/J-96 values are byte-identical, probe the live current as-of (a cache HIT), not a fresh-compute date that masks a stale-cache bug.
- **Why lean:** zero source diff, no backend/frontend/data-model boundary crossed, single verify-only flow. The prior evaluator did NOT emit ESCALATE (it emitted CONTINUE with an explicit lean recommendation), and iter-42 coherence was COHERENCE-PASS, so this is not a consolidation pass.
- **Why this is the closing half of the J-100 pair:** J-100's whole claim is a byte-identity property over RENDERED surfaces; iter-42 proved it at the compute layer (necessary, not sufficient). The framework auto-skipped the render proof on the backend-only flag. `Frontend Present: yes` here forces the live render capture in the SAME iteration so J-100 can flip without another round-trip (iter-36/42 lesson).
- **GOAL_ACHIEVED context (evaluator's call, not the decomposer's):** journey-history shows 87 passing + 9 already_passing + J-100 failing (held) + J-22/J-23/J-24 unknown (data-walled, NON-VETOING per goal.md:2445-2534). J-100 is the LAST unbuilt buildable Must-have (iter-22 lesson: diffed goal.md Must-have IDs J-01..J-100 against journey-history — all present, none newly-queued-unbuilt). Once J-100 flips passing on live evidence AND the full suite flushes `0 failed, EXIT 0` with zero regression and COHERENCE-PASS, the next evaluation is a sound GOAL_ACHIEVED candidate. Do NOT re-trigger the J-85 rebuild. The descoped `/api/data` warm-compute cost (~10-12s warm) is a documented, non-user-facing KNOWN-LIMITATION (single patient load, no polling) and does not block J-94/J-96 acceptance — the diagnostic and timeline ARE rendered and viewable.
- Closes open_item `iter35-api-data-timeline-uncached` (the perf root cause was fixed in iter-36/37/42; this iteration owes only the live-render closure).
