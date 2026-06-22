# Goal Iteration 46 — Live re-verification of the research labs + J-103 As-of on a quiet backend, flushed-suite confirmation (no code rework)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 46
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-103, J-104
- **Required-still-passing journeys:** J-29, J-25, J-26, J-77, J-91, J-90, J-63, J-65, J-51, J-72, J-32, J-101, J-102, J-97, J-98, J-18, J-07, J-06
- **Anti-goal reminders:**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The relocated as-of-scoped evidence aggregate is likewise derived once per resolved as-of date, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D.
  - **Single source of truth.** Each canonical value MUST be computed exactly once by the engine and read identically by every page; the API and frontend MUST NOT recompute it. The same value MUST NOT differ between two views. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only bars ≤ D; forward returns MUST use only bars > D. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias so results are never overstated.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable". *(critical)*
  - **Exactly one date selector (J-18).** No page-local or second date state may be introduced. *(critical)*
  - **No order/execution path.** No brokerage / order-placement / capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*

## GOAL

Capture genuine LIVE rendered evidence — on a freshly restarted, warmed, single-fetch-at-a-time backend — that the route-split research labs (J-104) and the Severity-velocity × Regime study (J-103, including its As-of mode driven by `?as_of=`) render their real figures and working N= drill-downs, byte-identical to pre-split, and confirm the full backend suite flushes `0 failed, EXIT 0` — turning the already-built J-103/J-104 into a sound GOAL_ACHIEVED candidate.

## BACKGROUND

J-103 and J-104 are already BUILT, CORRECT, and recorded passing — the iter-45 evaluator confirmed both (J-103 rendered live with a real 3×3 matrix + verbatim honest verdict + count-coherent N= drill-down; J-104's hub/route-split + lazy-load + byte-identical caching proven by `test_research.py`+`test_samples.py` 108/108 and `test_severity_velocity.py` 15/15 in isolation). The iter-45 verdict was CONTINUE, not GOAL_ACHIEVED, for two reasons only: (1) the browser-QA FAIL (19/25) was **not** a code regression — UT-03/UT-04 + UT-24/UT-25 skips were a **saturated/hung live backend** (PID 72189 still at ~25% CPU at eval time from earlier event-study hammering, so every heavy `/research/*` fetch returned the honest "Backend unavailable" no-fabrication banner), and UT-09 was a **wrong-param false-negative** (QA curled `?asof=` but the endpoint declares `as_of: Optional[str] = Query(...)`; the real frontend sends `as_of=`, and `test_as_of_filter_shrinks_pool_no_recompute` PASSES); (2) the standing flushed-GREEN full-suite gate is unmet (the suite hung at 98% with the documented warm-up/watchlist `.sssEEEEFFE.` contention tail — in `test_warmup.py`/`test_watchlist_persistence.py`, NOT the touched research code). This is the established iter-30→31 / iter-36→37 / iter-42→43 lean-reverify pattern, sixth repeat: NO code rework, just a clean live re-render on a quiet backend + the flushed suite. Every buildable Must-have (J-01..J-21, J-25..J-104) is otherwise positive-evidenced; only J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing per goal.md:105-108).

## IN SCOPE

This is a **verify-only** iteration. No source files change.

### Backend
- [ ] No code changes. (If the developer's diff is non-empty against HEAD, that is a defect — this iteration must land a zero-source-diff working tree.)

### Frontend (if applicable)
- [ ] No code changes. `Frontend Present: yes` is set ONLY to force the browser-QA render-capture step (the backend-only auto-skip blocker recurred on iters 36/39/42/43; iter-45 ran QA but against a hung backend). Do NOT edit any frontend file.

### New user-facing capability
None. This iteration produces verified evidence, not a feature.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. The surfaces under verification are the already-shipped `/research` hub + the seven lazy `/research/*` sub-routes (event-study, factor-lab, regime-setup-pattern, downtrend, recovery-turn-edge, severity-velocity, samples) and the unchanged Dashboard cross-view.

### Product surface delta
None — the product experience is unchanged; this confirms the iter-44/iter-45 deliverables render correctly under normal (non-saturated) conditions.

### Blueprint conformance
No new surfaces. All verified pages already have a canonical home in `blueprint.md`: the `/research` hub and its `/research/*` sub-routes (registered under the Research IA home at the iter-45 route-split), the Dashboard cross-view, `/stocks`, and `/research/samples`. No Information-Architecture or nav-skeleton change.

### Data-contract additions
None. This iteration introduces NO new displayed value. Every value re-verified (severity_velocity, regime label/score, forward_returns, event-study aggregates, N= sample counts) reads from its already-registered single canonical computing module + serving endpoint. No second computation or endpoint is introduced.

## OUT OF SCOPE

- Any code change (backend or frontend). If a genuine defect surfaces during live QA, record it and STOP — do not patch it in this verify-only lean pass; the evaluator will scope a follow-up.
- Re-triggering the J-85 `kind:rebuild` (~11h destructive; the snapshot data is correct — do NOT run it).
- J-22/J-23/J-24 — data-walled (no reachable cap-capable / intraday provider on this host); they stay honestly blocked-NA and NON-VETOING per goal.md:105-108. Do not attempt to "unblock" them here.
- Concurrent / parallel probing of heavy `/research/*` or `/api/data` endpoints (pool-exhaustion / hung-backend lesson — exactly what produced the iter-45 false failures). One heavy fetch at a time.

## DEFINITION OF DONE

- [ ] Target journeys J-103, J-104 confirmed passing via browser-qa-agent on **genuine live rendered evidence** captured against a freshly restarted, warmed, single-fetch-at-a-time backend — NOT a "Backend unavailable" / "Loading…" / skeleton frame.
- [ ] Each relocated `/research/*` lab renders its real figures + a working N= drill-down (J-104), byte-identical to pre-split; J-103's As-of mode re-verified IN THE BROWSER (toggle "As of date" at `?asof=2022-12-31`; rendered N values DECREASE vs all-history) — closing the UT-09 false-negative with positive rendered evidence.
- [ ] Required-still-passing journeys remain green (live smoke where they have a rendered surface; isolated-test corroboration otherwise).
- [ ] No anti-goal violation introduced (trivially: zero source diff).
- [ ] The FLUSHED full backend suite prints `0 failed, EXIT 0` from a `nohup`-async re-run on the now-quiet host — re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` E/F before attributing it (documented slow-boot / warm-up contention flake).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-46-dev.md` (stating "verify-only — zero source diff").

## TESTING REQUIREMENTS

- **Browser (capture LIVE rendered pixels, md5sum the evidence dir FIRST, reject blank/skeleton/byte-identical frames):**
  - **J-104** — `/research` hub renders 7 cards firing 0 research calls; each of the seven `/research/*` sub-routes (event-study, factor-lab, regime-setup-pattern, downtrend, recovery-turn-edge, severity-velocity, samples) returns HTTP 200 and renders **real figures** (not the "Backend unavailable" banner); exactly one heavy fetch fires per page; sidebar highlight via `startsWith`.
  - **J-103** — `/research/severity-velocity` renders the regime-family × velocity-sign matrix with real n / mean / win-rate cells; the verbatim honest verdict ("NOT supported" + "bounce, not continuation" + survivorship + bull-dominated + underpowered-for-crashes); a zero-N cell shows honest NA; an N= chip opens `/research/samples` in a new tab with total == the chip's N. **As-of leg:** toggle the "As of date" mode at `?asof=2022-12-31` and confirm the rendered N values DECREASE relative to all-history (the frontend sends `as_of=` automatically — do NOT re-curl `?asof=`).
  - **J-29** event-study (UT-04 re-do), **J-25/J-26** factor-lab (UT-03 re-do), **J-77** regime-setup-pattern, **J-91** downtrend, **J-90** recovery-turn-edge — each relocated lab's figures byte-identical to pre-split, N= drill-down works (**J-51/J-65** count-coherence: total == row n in Episodes + Pooled and All-history + As-of).
  - **J-18** (CRITICAL) — 0 native `input[type=date]` on `/research/*`; the severity-velocity As-of toggle is a MODE, not a second date state.
  - **J-07** (CRITICAL) — Risk-Off → 0 Actionable (the `/api/runs` invariant; research-only diff does not touch it).
  - **J-101 / J-102 / J-97 / J-98** — Dashboard cross-view + severity-velocity line/tooltip unchanged (byte-unchanged surfaces; quick smoke).
- **Unit/integration:** No new tests (verify-only). The GOAL_ACHIEVED gate is the FLUSHED full suite `0 failed, EXIT 0`. For corroboration if the live backend is again contended, re-run in isolation on the quiet host: `test_research.py` + `test_samples.py` (event-study, downtrend, recovery, samples count-coherence — J-29/J-63/J-91/J-90/J-51/J-65), `test_severity_velocity.py` (J-103 as_of-filter + cache byte-identity — 15/15), `test_no_magic_numbers.py`, `test_db.py::test_create_all_produces_expected_tables`.
- **Error cases:** Zero-N matrix cell → honest NA (no fabricated figure). A heavy `/research/*` fetch that fails under load → honest "Backend unavailable" no-fabrication banner (correct behaviour, NOT a journey failure — but if it appears, the backend is contended: restart + re-capture, do not record FAIL).

## NOTES

- **Operational prerequisite (do this FIRST):** Kill any hung/saturated live uvicorn from the prior iter (the iter-45 PID 72189 was still pegging CPU at eval time — kill **by port** :8835 per MEMORY "Dev server cleanup by port"; never broad-pkill on this multi-project machine). Bring up a fresh `:8835` and WAIT for `GET /api/health` "ready" so the warm-up daemon finishes (a cold pre-warm `/api/data` still pays ~10-12s by design — single patient load, NEVER concurrent probes, MEMORY pool-exhaustion lesson). Then `:3835`, `:9222`. The iter-45 browser-QA ran against a saturated backend, which is the SOLE cause of UT-03/UT-04/UT-24/UT-25 — a quiet, warmed backend is the entire fix.
- **PLAN the Playwright fallback UP FRONT** (do not wait for Chrome MCP CDP to time out). Chrome MCP CDP has emptied/contended the evidence dir on iters 38/39/40/42/45; the ONLY iters that captured live evidence (34/37/40/43) did so via the pre-planned Playwright fallback. `md5sum` the evidence dir FIRST and reject any blank / "Checking backend…" / "Loading…" / "Backend unavailable" / byte-identical frame as non-evidence (iter-18/33/44 capture-hygiene lessons).
- **Lesson — UT-09 param spelling (iter-45):** the severity-velocity endpoint declares `as_of: Optional[str] = Query(...)` (underscore). A curl of `?asof=` is silently dropped → `asof_date: null` is the CORRECT all-history response, NOT a bug. Re-verify the As-of leg IN THE BROWSER via the "As of date" toggle (the frontend's `fetchSeverityVelocity` → `withAsOf` → `as_of=` sends the right param); do NOT trust a curl-based "ignores param" result.
- **Lesson — hung-backend vs regression (iter-45):** when browser-QA shows "Backend unavailable" / HTTP 500 / timeout on the heavy `/research/*` labs, FIRST check whether the live backend is hung (CPU still pegged) and re-run the touched modules in isolation before calling REGRESSION. The labs' honest no-fabrication error state under load is correct behaviour, not breakage.
- **Lesson — suite gate (iter-11/29/30/37/45):** the iter-45 `.sssEEEEFFE.` tail lives in `test_warmup.py` / `test_watchlist_persistence.py` (slow-boot / warm-up contention flake), NOT the touched research code. Run the full suite `nohup`-async via the pump; NEVER block the evaluator on the in-flight suite; gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line; re-run any single E/F in isolation on the quiet host before attributing it.
- **Lesson — backend-only render auto-skip (iter-36/39/42/43):** `Frontend Present: yes` is set here specifically so browser-QA does NOT auto-skip on a zero-frontend-diff basis — the journeys under verification are RENDERED surfaces whose acceptance requires live pixels, and there is genuinely no frontend file to edit. Do not interpret the `yes` flag as a request for frontend code changes.
- **Outcome framing for the evaluator:** After the relocated labs + J-103 As-of re-render green on a quiet backend AND the full suite flushes `0 failed, EXIT 0`, the next evaluation is a sound GOAL_ACHIEVED candidate — every buildable Must-have (J-01..J-21, J-25..J-104) positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA (data-walled, NON-VETOING per goal.md:105-108; J-22 auto-unblocks via the already-built+passing J-84 cookie+crumb expand path with NO code change once a cap-capable provider is reachable). Do NOT re-trigger the J-85 `kind:rebuild`.
