# Goal Iteration 4 — Closure / re-verify the five partial journeys (J-02, J-06, J-11, J-15, J-16)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 4
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-02, J-06, J-11, J-15, J-16
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-07, J-08, J-09, J-10, J-12, J-13, J-14, J-17, J-18, J-19
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. *(extends Single source of truth)*
  - **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and MUST NOT by itself promote a name to "Actionable"; it rides as a separate flag computed once per run, price+volume only, with date ≤ D (no-lookahead), and is part of the immutable snapshot. Its detection thresholds MUST come from config (no magic numbers). *(critical — protects Single source of truth + Risk-Off gating)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*

## GOAL

Convert the five remaining `partial` journeys (J-02, J-06, J-11, J-15, J-16) to **passing** by driving each through its **full multi-step acceptance flow** against surfaces that are already built — no new feature code — so the evaluator can reach **GOAL_ACHIEVED**.

## BACKGROUND

All 19 must-have journeys are built: J-17 (Data Manager), J-18 (one date control), J-19 (attribution) landed in iters 1–3 and are passing; zero journeys are `failing`. Five journeys remain `partial` **only because their full multi-step acceptance flows were never exercised** — iter-2's `TC-17` captured the surfaces in single screenshots, and iter-3 deliberately left them out of scope (it was the J-17 build). The iter-3 evaluator's explicit next-step is this planned **closure / re-verify pass at lean depth**: browser-QA-driven verification of already-built surfaces, not feature work.

A source scan this iteration confirms every surface exists and is wired to the canonical values:
- **J-02 / J-16** — `apps/frontend/app/stocks/page.tsx`: Sector filter (`aria-label="Filter by sector"`), Setup filter (`Filter by setup status`), VCP filter (`Filter by VCP pattern`, "VCP only" / "Non-VCP"); client-side **re-display only** (`rows.filter(...)`, lines ~129–135 — never re-sorts or recomputes a score/flag); explicit empty-state ("No rows are fabricated to fill the view").
- **J-16 (System Health)** — `apps/frontend/app/system-health/page.tsx`: a "Forward return: VCP vs non-VCP" panel reading `data.by_vcp`.
- **J-11** — `apps/frontend/app/watchlist/page.tsx`: the Add form (ticker + reason inputs, `Add` button → `addWatchlistEntry`); backend `POST /api/watchlist` persists `created_at` to the SQLite `Watchlist` table (survives a process restart).
- **J-06 / J-15** — the watchlist module and the Data Contract confirm the leaderboard and detail page read the **same** stored snapshot row (`scoring:score_stocks` → `GET /api/stocks` and `GET /api/stocks/{ticker}`); reads are snapshot-served.

This grounds the pass: the five are unverified, not unbuilt.

## IN SCOPE

### Backend
- [ ] **None — verification only.** No backend code change is expected. **Contingency:** if a full-flow run reveals a *genuine functional gap* (e.g. a filter that does not narrow rows, a watchlist entry that does not persist across restart, a missing invalidation level, a fabricated number where NA is required), fix that **specific** gap surgically and add/extend the one matching test. If the gap needs more than a trivial fix, flag it in the handoff for escalation to **full** depth — do not add features or refactor.

### Frontend
- [ ] **None — verification only** (same contingency as Backend). Any fix must be surgical, trace to a specific journey acceptance criterion, and not "improve" adjacent code.

### New user-facing capability
None — this is a closure / verification pass. The product's capabilities are unchanged; this iteration establishes end-to-end evidence that the already-built flows work.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None directly. The value of this iteration is **evidence**: the five flows are proven through their full click-paths, closing the session.

### Blueprint conformance
No new surfaces and no new contract values. The blueprint already lists every journey home for these five as **built**: `/stocks` (J-02, J-16), `/stocks/[ticker]` (J-06), `/watchlist` (J-11), `/system-health` (J-16 by-VCP), and the cross-cutting `snapshot_serving` (J-15). The nav skeleton is unchanged → **no re-approval requested**. This iteration makes only **stale-status accuracy edits** to `blueprint.md` (J-18 markers `⚠`→built/resolved; J-19 `building iter-2`→`built iter-2`; invariant #5 "currently violated" parenthetical removed) so the coherence contract reflects reality before a potential GOAL_ACHIEVED.

### Data-contract additions
**None.** Every value these journeys display is already registered and is read from its single canonical source: the six scores + A–E bucket + setup status (`scoring:score_stocks` / `buckets:to_bucket` / `setups:classify_setup` via `GET /api/stocks` and `/api/stocks/{ticker}`); the VCP flag (`patterns:detect_vcp`); the VCP-vs-non-VCP forward-return breakdown (`forward_testing:compute_forward_aggregates` → `GET /api/system-health`, `by_vcp`); the watchlist entry (`GET /api/watchlist`); snapshot-served reads (`snapshot_serving`). The journeys **read** these — they introduce no new or second computation.

## OUT OF SCOPE

- Any new feature, page, endpoint, model, or contract value.
- Refactoring, restyling, or "improving" the existing five surfaces.
- The nice-to-haves: editing config weights from a UI view (cap 14); historical score charts (cap 15).
- Any change to the global as-of control, the default boot path, or any scoring / return / bucket math.
- Re-running the full backend suite when nothing changed. **If** a surgical fix is made, run the *targeted* tests for it (the full pytest suite is ~14 min — do not run it speculatively, and do not run two pytest invocations concurrently).
- Converting a `partial` by a single-screenshot surface check (the iter-2 lesson) — only a full multi-step flow counts.

## DEFINITION OF DONE

- [ ] **J-02 passes** — `/stocks` renders multiple ranked rows, each with ticker, Leadership / Entry Quality / Risk (A–E bucket **+** number), a setup status, and a **non-empty reason**; selecting a single Sector reduces the visible rows to that sector only; selecting Setup = **Actionable** shows only Actionable rows (or an explicit empty-state if none in the current snapshot).
- [ ] **J-06 passes** — NVDA's Leadership, Entry Quality, and Risk scores **and** their A–E buckets are **identical** on `/stocks` and `/stocks/NVDA` (one computed value per score, never recomputed per view).
- [ ] **J-11 passes** — add `ANET` with a free-text reason; it appears immediately with date-added, the reason, current Leadership/Entry/Risk + setup, a price-since-added figure, and an invalidation level; after a **backend RESTART** the entry is still present (persisted in SQLite, not in-memory).
- [ ] **J-15 passes** — `/stocks` reaches interactive within the **~1.5 s warm-load** budget (warm = route already compiled; see the dev-server note) and its values remain identical to `/stocks/NVDA` (coherence preserved); the rows come from the stored snapshot, not a per-request recompute.
- [ ] **J-16 passes** — the VCP filter shows only flagged names (or an explicit empty-state); each flagged row shows the VCP badge + reason + a concrete invalidation level (pivot / last-contraction low); a flagged stock's detail page shows the VCP badge with its pivot/invalidation; `/methodology` lists VCP with its meaning, the config thresholds, and an example; `/system-health` shows mean forward returns for VCP vs non-VCP with sample size n (NA below the min-sample threshold). The VCP flag reads identically on leaderboard and detail and **never makes a name Actionable on its own**.
- [ ] **Required-still-passing journeys remain green** — J-01, J-03, J-04, J-05, J-07, J-08, J-09, J-10, J-12, J-13, J-14, J-17, J-18, J-19; spot-check the criticals (J-07 zero Actionable in a Risk-Off run, J-18 exactly one date control, J-13 as-of switcher).
- [ ] **No anti-goal violation introduced; coherence stays COHERENCE-PASS.**
- [ ] **Dev handoff** at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-4-dev.md`. If zero code changed, it states so explicitly (no-op developer pass — the value is the browser-QA evidence). If a surgical fix was made, it lists the exact change + the targeted test result.

## TESTING REQUIREMENTS

- **Browser (full multi-step flows — NOT single-screenshot surface checks; iter-2 lesson):**
  - **J-02:** load `/stocks` → confirm ranked rows each with ticker + three bucketed scores + setup + non-empty reason → pick one Sector → confirm rows reduce to that sector → pick Setup = "Actionable" → confirm only Actionable rows (or an explicit empty-state) → clear filters and confirm rows return. Capture distinct before/after-filter screenshots.
  - **J-06:** record NVDA's three scores + buckets on `/stocks`; open `/stocks/NVDA`; assert each of the three is byte-identical (number and bucket).
  - **J-11:** open `/watchlist` → add `ANET` with a reason → confirm date-added / reason / current score+setup / price-since-added / invalidation all render → **restart the backend** → reload `/watchlist` → confirm `ANET` still present with the same fields.
  - **J-15:** **warm-load** `/stocks` — first navigate to it once so the dev route compiles, then measure a **second** load/navigation reach-interactive against ~1.5 s; record the number. Confirm the leaderboard values equal `/stocks/NVDA` (coherence). Exclude first-compile time (see note).
  - **J-16:** `/stocks` → apply VCP filter → flagged rows show badge + reason + invalidation (or explicit empty-state) → open one flagged stock's detail, confirm the VCP badge + pivot/invalidation → `/methodology` confirm the VCP entry (meaning + config thresholds + example) → `/system-health` confirm the VCP-vs-non-VCP forward-return panel with n (NA below min-sample).
- **Unit/integration:** none required (no code change expected). If the contingency fires and a surgical fix is made, add/extend the single matching test and run it **targeted** (not the full ~14 min suite).
- **Error cases (verify honest behavior — never fabricate to force green):**
  - J-02: a filter combination with no matches must show the explicit empty-state, **not** fabricated rows.
  - J-16: a VCP / non-VCP cohort below the min-sample threshold must show NA + n, **not** a fabricated 0%.

## NOTES

**Lessons applied (`lessons.md`):**
- *iter-2:* a single screenshot proves a surface EXISTS but does NOT satisfy a multi-step acceptance flow — all five MUST be driven through their full click-paths to convert from `partial`.
- *iter-2 (J-19 / coherence):* on `/backtest` the distribution-panel mean is over the FULL observed set at the selected horizon and **legitimately differs** from the scorecard's top-ranked-cohort mean shown above it (different populations). The `distribution.mean == overall.mean` invariant binds ONLY the `/system-health` aggregate. If a regression spot-check wanders onto `/backtest`, do **not** flag that per-date mismatch as an inconsistency.
- *iter-1:* the global as-of date lives in an **in-memory** app-shell provider (`components/asof-provider.tsx`) — it survives client-side navigation but resets to Latest on a hard reload. For **J-15**, the warm load is a **second client-side navigation** to an already-compiled route (not a hard reload). For **J-11**, the restart is a real **backend process** restart — persistence is in SQLite, not the in-memory frontend state — so reload `/watchlist` after the restart and confirm the data returns from `GET /api/watchlist`.
- *iter-0:* never trust a browser-QA *negative* finding on degraded tooling — confirm against source. Pre-confirmed this iter: all five surfaces exist and are wired to the canonical values (see BACKGROUND).

**J-15 dev-server timing caveat (important for a fair pass):** browser-QA starts the frontend with `npx next dev` (`scripts/start-frontend.sh:28`). A Next.js **dev** server compiles each route on its first request, so a **cold** first load of `/stocks` can take several seconds purely from compilation — that is **not** the snapshot-serving latency J-15 is about. Measure the **warm** load: hit `/stocks` once to compile it, then measure a **second** reach-interactive against the ~1.5 s budget. The enforceable J-15 guarantee is **structural** — rows are served from the persisted snapshot (no per-request recompute) and values stay identical to the detail page (coherence) — and the ~1.5 s is approximate. Record the warm number honestly with this caveat; a production build (`npm run build && npm start`) is the fair timing reference but is not required to be set up here. If the warm number is borderline purely due to the dev server, the evaluator should weight the structural guarantee.

**Backend restart for J-11 (machine safety):** restart the backend **by port** (default `8835`, honoring `CHAIN_BACKEND_PORT`) — never a broad `pkill -f uvicorn` on this multi-project machine. The QA harness manages start/stop; if restarting manually, target the port only.

**This is the FINAL planned iteration.** If all five convert and nothing regresses (J-17/J-18/J-19 + the rest stay green, coherence PASS), the evaluator's verdict should be **GOAL_ACHIEVED**. Escalate to **full** depth ONLY if a `partial` turns out to be a genuine functional gap needing non-trivial code — not merely unverified.
