# Goal Iteration 5 — Closure re-verify: convert J-06, J-11, J-15 (hardened against the iter-4 browser-QA timeout)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 5
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-06, J-11, J-15
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09, J-10, J-12, J-13, J-14, J-16, J-17, J-18, J-19
- **Anti-goal reminders (directly binding this iteration, verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)* — **this is exactly what J-06 verifies.**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. *(extends Single source of truth)* — **this is the structural basis of J-15.**
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. — **J-11 persistence and J-15 timing must be real, not faked; do not fabricate a screenshot or a number.**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)* — cross-cutting; J-15 navigates multiple date-scoped pages.
  - All other anti-goals in `docs/goal.md` remain in force verbatim and binding — **No lookahead** *(critical)*, **Snapshots are immutable** *(critical)*, **No magic numbers**, **No order/execution path** *(critical)*, **No secrets in source**, **Risk-Off must gate Actionable** *(critical)*, **Scores must be explainable**, **Honest limitations surfaced**, no auth tokens in `localStorage`, **On-demand snapshots stay immutable & lookahead-free** *(critical)*, **Setup & pattern vocabulary is config-driven in the UI too**, **Honest forward-test for partial windows**, **VCP is a pattern, not a status** *(critical)*, **Live fetch is real-data-only**, **Range backfill stays immutable & lookahead-free**, **Attribution is read-only**. A zero-code re-verify introduces none of these; the coherence-auditor + evaluator re-confirm they hold.

## GOAL

Convert the three remaining `partial` journeys to `passing` by capturing their **defining** browser-QA steps — J-06 (the three scores byte-identical on `/stocks` and `/stocks/NVDA`), J-11 (the watchlist entry still present **after a real backend restart**), and J-15 (a measured **warm** load of `/stocks` from the persisted snapshot) — with the run hardened against the iter-4 timeout, so the evaluator can declare **GOAL_ACHIEVED**.

## BACKGROUND

Sixteen of the nineteen must-have journeys are `passing`/`already_passing`; only **J-06, J-11, J-15** remain `partial`. Per the iter-4 evaluation, all three are **already built and structurally verified** in source and at the API/DB level (`snapshot_serving.py` serves the same stored row to `/api/stocks` list and detail → J-06; the `Watchlist` SQLModel row was read back off SQLite disk by a separate reader → J-11; reads are snapshot-served with no per-request recompute → J-15). The **only** gap is evidence capture: the iter-4 browser-QA step **timed out (exit 124, SKIPPED stub)** during/after the J-11 backend restart, so J-11's after-restart shot, J-15's warm-load timing, and J-06's both-numbers-legible coherence capture were never recorded. This is a **tooling failure, not a functional gap** (iter-4 lesson), so depth is **lean** and **no code is changed** — the iter-4 dev pass changed zero source/config/frontend/schema files (coherence-auditor confirmed) and this iteration must do the same; introducing code is scope creep. The iter-4 lesson is applied structurally: run the two **no-restart** journeys (J-06, J-15) first and **flush evidence incrementally**, so a restart hang during J-11 cannot lose earlier passes.

## IN SCOPE

This is a **verify-only** iteration. The `developer` agent is expected to be a **NO-OP** (zero source/config/frontend/schema diff, exactly like iter-4). The value comes entirely from the `browser-qa-agent` capturing the three defining flows.

### Backend
- [ ] None — no backend code change. (All J-06/J-11/J-15 backend paths exist and are verified: `apps/backend/app/api/stocks.py`, `apps/backend/app/engine/snapshot_serving.py`, `apps/backend/app/api/watchlist.py` + `Watchlist` model at `apps/backend/app/models.py:243`.)

### Frontend
- [ ] None — no frontend code change. (Pages exist: `apps/frontend/app/stocks/page.tsx`, `apps/frontend/app/stocks/[ticker]/page.tsx`, `apps/frontend/app/watchlist/page.tsx`.)

### New user-facing capability
None — every capability is already shipped. This iteration closes the **evidence** for three journeys; it adds no product capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The product experience is unchanged; this iteration only records browser proof that three already-built flows work end-to-end.

### Blueprint conformance
No new surfaces. All three journeys' canonical homes are already registered in `blueprint.md` as `[built]`: J-06 `/stocks ↔ /stocks/[ticker]`, J-11 `/watchlist`, J-15 cross-cutting (`snapshot_serving`). **No blueprint edit and no nav-skeleton change are required**, so no `blueprint.reapproval-requested` is written.

### Data-contract additions
None. No new displayed value is introduced. J-06/J-11/J-15 read **existing** registered contract values from their existing canonical endpoints (Leadership/Entry Quality/Risk from `GET /api/stocks` + `GET /api/stocks/{ticker}`; the watchlist entry from `GET /api/watchlist`). Do not introduce a second computation or endpoint for any of them.

## OUT OF SCOPE

- **Any source / config / frontend / schema change.** The three journeys are built and structurally verified; only browser evidence is missing. Changing code here is scope creep and a regression risk.
- **Full re-test of the 16 already-green journeys.** Spot-check coherence only (see Testing). Zero code changes this iteration ⇒ no regression is possible.
- **Escalation to `full` depth.** The blocker is a QA-runner timeout, not a functional gap needing code (iter-4 lesson). Do not escalate.
- **Any live-provider / Data Manager fetch, weight tuning, or new test authoring.** Not needed for closure.

## DEFINITION OF DONE

- [ ] **J-06** passes via `browser-qa-agent`: a `/stocks` capture and a `/stocks/NVDA` capture, **both with the three scores legible (not thumbnails)**, show identical Leadership, Entry Quality, and Risk (A–E bucket **and** 0–100 number) on both pages.
- [ ] **J-11** passes via `browser-qa-agent`: `ANET` is added with all fields, the backend is **restarted by port** (not a broad kill), and after the restart `/watchlist` still shows `ANET` — captured in `UT-J-11-after-restart.png`.
- [ ] **J-15** passes via `browser-qa-agent`: a **warm** (second, route already compiled) load of `/stocks` is measured and the number recorded; leaderboard values equal `/stocks/NVDA` (coherence); if the dev-server warm number is borderline vs ~1.5 s, the structural snapshot-served guarantee (no per-request recompute, verified in `snapshot_serving.py`) is cited honestly alongside the measured number.
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09, J-10, J-12, J-13, J-14, J-16, J-17, J-18, J-19) remain green — no regression (guaranteed by zero code change; coherence-auditor re-confirms).
- [ ] No anti-goal violation introduced (zero-code pass; coherence-auditor = COHERENCE-PASS).
- [ ] Unit tests still pass (no code changed; a sanity run, not new tests).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-5-dev.md` documenting the NO-OP (zero files changed) and pointing to the three flows that browser-QA must capture.

## TESTING REQUIREMENTS

- **Browser (the heart of this iteration):** verify **J-06, J-11, J-15** in the order below. Run J-06 and J-15 (no restart) **first** and write their result lines **before** starting J-11. Save each screenshot to the evidence dir immediately after capture; do not batch at the end.

  **Order 1 — J-06 (score consistency, no restart):**
  1. Open `/stocks` (latest as-of). Locate the `NVDA` row; ensure it is **legible** (scroll/scope so the three scores are readable, not a zoomed-out thumbnail). Capture `UT-J-06-leaderboard-nvda.png` and note NVDA's Leadership, Entry Quality, Risk (bucket + number).
  2. Click the `NVDA` row → `/stocks/NVDA`. **Scroll to the three score cards** so Leadership, Entry Quality, and Risk (each bucket + 0–100) are fully visible. Capture `UT-J-06-detail-nvda-scores.png`.
  3. Assert the three values (bucket **and** number) are **identical** across the two captures. The two screenshots must be distinct images (no byte-identical duplicate — iter-3 lesson).

  **Order 2 — J-15 (warm load, no restart):**
  1. Navigate to `/stocks` once to compile the route (dev mode) — **discard** this first timing.
  2. Navigate away (e.g. to `/`) then **back to `/stocks` via in-app client-side nav** and measure time-to-interactive of this **warm** load. Record the number. (Prefer in-app nav over a hard reload for the timing; note that a hard reload resets the in-memory as-of to Latest — fine here since J-15 tests the latest date — iter-1 lesson.) Capture `UT-J-15-warm-load.png`.
  3. Confirm the leaderboard values equal `/stocks/NVDA` (reuse the J-06 observation) — coherence preserved, rendered from the stored snapshot.
  4. If the measured warm number is borderline above ~1.5 s on the dev server, record it **honestly** and cite the structural guarantee: reads are snapshot-served with **no per-request recompute** (`apps/backend/app/engine/snapshot_serving.py`). Do not fabricate a passing number.

  **Order 3 — J-11 (persistence across a REAL restart — do last; the restart is the timeout risk):**
  1. Open `/watchlist`. Add `ANET` with reason `"ANET — strong leader, watching pullback"`. Confirm it renders with date-added, reason, current Leadership/Entry/Risk + setup, price-since-added, and an invalidation level. Capture `UT-J-11-before-restart.png`. **Flush this result note now.**
  2. **Restart the backend by PORT, bounded so it cannot hang the runner** (memory + iter-4 lesson — never a broad `pkill -f uvicorn`/`next dev` on this multi-project machine):
     ```bash
     PORT="${CHAIN_BACKEND_PORT:-8835}"
     # kill ONLY the process bound to the backend port:
     fuser -k "${PORT}/tcp" 2>/dev/null || (lsof -ti "tcp:${PORT}" | xargs -r kill)
     # restart (backgrounded) and wait for health, BOUNDED (max ~30s, then proceed/fail cleanly — never block forever):
     bash scripts/start-backend.sh >/tmp/iter5-backend.log 2>&1 &
     for i in $(seq 1 30); do curl -sf "http://localhost:${PORT}/api/health" >/dev/null && break; sleep 1; done
     ```
  3. Reload `/watchlist` and confirm `ANET` is **still present** with its fields. Capture `UT-J-11-after-restart.png` (the defining proof — DB persistence, not in-memory). **Flush this result note.**

- **Unit/integration:** no new tests. As a sanity check only, the existing backend suite should still pass (no code changed). Per machine memory, the full pytest run is heavy (~14 min, walk-forward boot) and only one pytest invocation may run at a time — a sanity subset is acceptable; do not run two concurrently.
- **Error cases:** none new (no new code path). J-11's no-fabrication property is already covered; J-15's no-recompute property is structural.

## NOTES

- **Why lean, not full (iter-4 lesson, applied):** a browser-QA `exit 124` timeout that leaves a SKIPPED stub `ui-test-results.md` is a **tooling failure**, not a functional gap. All three journeys are built and verified in source/API/DB; escalate to `full` only for genuine missing code — there is none here.
- **Don't trust the stub; reconcile with the evidence dir (iter-4 lesson):** if `ui-test-results.md` is again a SKIPPED/stub but the `*-evidence/` dir has shots, inspect the directory and screenshot timestamps directly; convert a `partial` **only** if its **defining** step was actually captured (J-06 = both numbers legible on both pages; J-11 = the after-restart shot; J-15 = a real warm-load number).
- **Harden the run against the iter-4 timeout:** (a) do the two no-restart journeys first and **write/flush each journey's result immediately** so a later hang loses nothing; (b) the J-11 restart is **bounded** (kill by port; health-poll capped at ~30 s) so it cannot block the runner indefinitely — the iter-4 hang occurred during/after the restart; (c) keep total browser work minimal (three journeys) to stay well under the step timeout.
- **Restart hygiene (machine memory):** on this multi-project machine, **never** broad-kill `next dev`/`uvicorn`; always kill by the project port (`CHAIN_BACKEND_PORT`, default `8835`). The backend may currently be down (nothing on `:8835` after iter-4) — start it before the browser flows.
- **Evidence hygiene (iter-3 lesson):** every screenshot must be a **distinct** capture; do not ship byte-identical images (iter-3 shipped a "summary" shot that duplicated the "running" shot). J-06 in particular needs two genuinely different, legible captures.
- **Coherence:** zero source/config/frontend/schema change is expected → coherence-auditor should return COHERENCE-PASS with only bookkeeping/status-text edits. If any code change appears in the diff, that is out-of-scope and must be reverted before evaluation.
- **Outcome:** if all three convert via their full UI flows and nothing regresses (coherence stays PASS), the next evaluator verdict should be **GOAL_ACHIEVED** (17 passing + J-06/J-11/J-15 = all 19 must-have journeys green, J-12 `already_passing`).
