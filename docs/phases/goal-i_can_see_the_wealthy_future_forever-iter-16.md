# Goal Iteration 16 — J-31 synthesis capstone: capture the cross-page browser travel (lean re-verify, no code change expected)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 16
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-31
- **Required-still-passing journeys:** J-25, J-27, J-29, J-30 (lab evidence the travel reads), J-29/J-28/J-16 (the subjects/patterns the cross-link filters to), J-02 (the deep-linked leaderboard filter), J-05, J-06, J-20 (the Stock-Detail end of the travel), J-18 (the principal anti-goal risk — exactly one date selector), J-15 (warm load — filters must not refetch)
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. The Stock-Detail chart **timeframe selector** (1D/1h/15m/5m) is NOT a date control — it changes bar granularity only, bounded by the resolved as-of date. *(extends Single source of truth — THE principal risk this iter, since `/stocks` carries URL filter params)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. (Here: weak/low-sample lab evidence and a zero-match filter MUST stay honest NA / empty-state — never a fabricated number or filter.)
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure MUST be derived once from stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label.

## GOAL

Capture the J-31 synthesis travel end-to-end in the browser — Factor Lab + Setup & Pattern Lab evidence → "View the names expressing this on the leaderboard →" cross-link → pre-filtered `/stocks` (DOM-asserted) → open a row → `/stocks/[ticker]` detail — on a clean, hydrated frontend, converting J-31 from `partial` to `passing` with no code change.

## BACKGROUND

J-31 (the synthesis capstone — the last buildable journey) was **built** in iter-15 exactly as specified: a frontend-only +89/−4 diff across the two intended files (`stocks/page.tsx` URL-deep-linkable filters behind the Next-15 `<Suspense>` boundary; `research/page.tsx` `SubjectLeaderboardLink`). The evaluator source-verified the principal anti-goal risk (J-18) clean and recorded review PASS_WITH_NOTES, coherence COHERENCE-PASS, backend 453 passed/4 skipped, build/typecheck PASS. The feature is committed (iter-15) and still present in the tree (re-confirmed this plan: `SubjectLeaderboardLink` at `research/page.tsx:1002`; `Suspense`/`useSearchParams`/`parsePatternParam`/`router.replace` in `stocks/page.tsx`).

**The single gap:** J-31's defining acceptance is the **full multi-step cross-page browser travel**, and that travel was never captured — browser-QA returned **SKIPPED** because the iter-15 DoD step `npm run build` clobbered the running `next dev` server's `.next`, serving a dead, un-hydrated shell on every route (an environmental fault — MEMORY `browser-qa-dead-shell-next-cache` — not a code defect). Per the iter-4 lesson the evaluator cited, a partial is converted to passing ONLY when the defining step is actually captured, so J-31 stayed `partial`. The evaluator's verdict was CONTINUE with an explicit recommendation: **a lean re-verify of J-31 only, hardened against the `.next` clobber, no code change expected.** This iteration executes that — its whole value is the captured travel on a clean, hydrated build.

## IN SCOPE

### Environment remediation (PRE-TEST — no source change; this is the actual blocker)

- [ ] **Fix the `.next` clobber before any browser test.** Stop the frontend dev server **by port** (frontend `3835` / `CHAIN_FRONTEND_PORT`) — do NOT broad-`pkill -f "next dev"` (multi-project machine; MEMORY `dev-server-cleanup-by-port`). Then `rm -rf apps/frontend/.next` and restart `next dev`.
- [ ] **Do NOT run `npm run build` against the live dev server's `.next` at any point this iteration.** That is the iter-15 root cause: a production build overwrites the dev server's unhashed chunks with content-hashed prod chunks → `GET /_next/static/chunks/main-app.js` 404 → no hydration on every route. The committed build was already proven sound in iter-15 (build/typecheck PASS) — do not re-verify it against the running dev `.next`. If a build check is genuinely wanted, run it in a separate/throwaway dir or BEFORE the dev server starts, never against the served `.next`.
- [ ] **Confirm the shell is alive before driving any UT case:** `GET /_next/static/chunks/main-app.js` → **200** (the smoking-gun check — absent unhashed `main-app.js` while a hashed `main-app-<hash>.js` + `BUILD_ID` + `build-diagnostics.json:static-generation` are present means the dead shell recurred), and the health badge has flipped OFF "Checking backend…" on a live route (rows render, not 0). Backend up on `8835` / `CHAIN_BACKEND_PORT`.

### Backend

- [ ] **None.** No backend change. The whole J-31 travel re-displays canonical stored values served by `GET /api/stocks`, `GET /api/research/event-study`, `GET /api/research/factor-lab`, `GET /api/stocks/{ticker}` — recompute nothing.

### Frontend

- [ ] **None expected.** The J-31 feature is built, committed, and present. Make a source edit ONLY if the captured travel surfaces a genuine functional defect in the already-built flow (e.g. a cross-link that mis-encodes a subject, or a filter param that fails to round-trip) — in which case fix it minimally and re-capture. Do not add scope.

### New user-facing capability

None new — this iteration *proves* the iter-15 capability (travel from lab evidence to the names expressing a factor/pattern today) by capturing it on a hydrated build.

### New information displayed

None. No new value, panel, or surface.

### New user actions

None. The "View the names expressing this on the leaderboard →" cross-link and the URL-deep-linkable filters already exist.

### UI surface changes

None. The travel spans existing approved homes: `/research` (Factor Lab + Setup & Pattern Lab) → `/stocks` (deep-linked filter) → `/stocks/[ticker]`.

### Product surface delta

No change to the product surface. The deliverable is verification evidence: a captured, hydrated, DOM-asserted walkthrough of the synthesis travel.

### Blueprint conformance

No new surfaces; no nav-skeleton change. The travel uses existing approved homes (`/research`, `/stocks`, `/stocks/[ticker]` — all in `blueprint.md` IA). The J-31 Feature/journey-homes row and the iter-15 nav-skeleton note are already current in `blueprint.md`. **No `blueprint.reapproval-requested` marker is written.**

### Data-contract additions

**None.** This iteration registers no new Data-Contract value. The `/stocks` URL params are a re-display control over already-registered values (`Leadership/Entry Quality/Risk` + setup status + detected-pattern flags, served by `GET /api/stocks`); the cross-link reads the already-registered event-study subject (`GET /api/research/event-study`). No second computation, no new endpoint — `blueprint.md` is already correct and needs no edit.

## OUT OF SCOPE

- **J-22 (~500-name universe), J-23 (multi-timeframe intraday bars), J-24 (chart timeframe selector)** — externally Yahoo-429 data-walled. **Do NOT autonomously retry the fetch.** J-22 auto-heals via its committed finish runbook only on operator confirmation of a reachable no-key egress; J-23/J-24 need the same external feed. Re-probing the wall again wastes a pipeline (re-confirmed iters 7, 8).
- Any new feature, panel, factor, pattern, endpoint, or surface.
- `npm run build` against the live dev `.next` (see Environment remediation — this is what broke iter-15).
- Re-exercising every carried-green journey in the browser. Only the J-31 travel + the journeys it crosses (Required-still-passing) need live capture; the rest are carried (no diff possible from a zero/near-zero source change).

## DEFINITION OF DONE

- [ ] **The frontend shell is confirmed hydrated** (`GET /_next/static/chunks/main-app.js` → 200; health badge cleared; rows render) BEFORE any UT case runs.
- [ ] **J-31 full travel captured green** by the browser-qa-agent under exclusive Chrome, with distinct (sha256-distinct) screenshots + DOM/network assertions at each step:
  1. `/research` Factor Lab — decile table (raw mean + downside-risk-adjusted column + n) + Spearman rank-IC + by-regime split render and re-point on a factor change (J-25/J-27/J-30 evidence).
  2. `/research` Setup & Pattern Lab — pick a **populated** subject and read its event study (distribution / expectancy / MAE-MFE / risk-adjusted / by-regime + by-sector), with honest NA + n on low-sample cells (J-29 evidence).
  3. Click **"View the names expressing this on the leaderboard →"** and land on `/stocks` with the deep-linked filter applied.
  4. **DOM-assert** the pre-applied filter and the narrowed `visible/total` count against ground truth (below).
  5. Open one filtered row → `/stocks/[ticker]` showing the pattern/setup badge, the three A–E scores (+ raw 0–100, ≥3 named components each), and the concrete invalidation level (J-05/J-06), with the price+MA chart through the latest date and the as-of marker (J-20).
- [ ] **J-18 live cross-check captured:** with a filter deep-linked on `/stocks`, toggle the global top-bar as-of switcher and assert — distinct shots + observed network — that (a) the filter stays intact, (b) the page re-points by date, and (c) **no `as_of`/date query param** appears in any leaderboard fetch and none is written to the URL (only `sector`/`setup`/`pattern`).
- [ ] **Required-still-passing journeys remain green** (J-25, J-27, J-29, J-30, J-28, J-16, J-02, J-05, J-06, J-20, J-18, J-15) — verified live where on the travel path, carried (untouched paths) otherwise.
- [ ] **No anti-goal violation introduced** (especially: exactly one date selector; read-only / no recompute; honest NA).
- [ ] **No regression:** backend unit suite stays green (no source change expected → trivially green; if a frontend fix was needed, re-run typecheck + the relevant tests). `git diff` is empty OR a minimal, intentional frontend-only fix.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-16-dev.md` (record: env remediation performed, whether any source change was needed, and the clean-shell confirmation).

## TESTING REQUIREMENTS

- **Pre-flight (gating, before any UT):** confirm `GET /_next/static/chunks/main-app.js` → 200 and a live route renders rows (health badge off). If the dead shell is present, remediate per Environment remediation and re-confirm — a dead-shell SKIP is environmental, never a code FAIL/regression (MEMORY `browser-qa-dead-shell-next-cache`).
- **Browser (J-31 — the defining capture):** drive the full travel above under **exclusive Chrome**. Serialize browser access against any concurrent QA/cross-project Chrome use (iter-6 lesson: the `qa` agent and the `browser-qa-agent` sharing one Chrome corrupted captures; cross-project Tapeology on `:3650` contends) — one agent vacates before the other captures; assert live DOM state (`data-testid="asof-indicator"`, the filter control, the URL, the visible/total count) immediately before each screenshot; **de-dup all evidence by sha256** (the iter-3/6 byte-identical-shot bug must not recur).
- **Ground-truth counts for the DOM assertion** (pre-captured in the iter-15 browser-QA report; use a populated subject so the narrowed count is non-trivial and the leaderboard isn't empty):
  - pattern `pullback_to_rising_dma` → **9** names
  - pattern `flat_base_breakout` → **3** names
  - pattern `vcp` → **4** names
  - setup `Breakout-watch` → **8** names
- **J-18 live (network-asserted):** deep-link a filter, toggle the global as-of; capture the network tab / request log and assert **zero** `as_of` (or any date) query param on the `/api/stocks` fetch and **zero** date param written to the page URL; the filter persists across the toggle.
- **Unit/integration:** none required if no source changes (the committed backend suite was 453 passed/4 skipped at iter-15; the FE typechecked). If a frontend fix is made, re-run `cd apps/frontend && npx tsc --noEmit` (or the project typecheck) and any affected test — **without** running a production `npm run build` against the live dev `.next`.
- **Error/honesty cases:** an unrecognized `pattern` URL param falls back to the `__all__` sentinel (no crash, no fabricated filter); a zero-match filter shows the existing honest empty-state; low-sample lab cells stay NA + n (never a fabricated number).

## NOTES

- **This is a verify-only re-run.** No code change is expected — the iter-15 feature is built, committed, statically sound (build/typecheck PASS), and source-verified clean for J-18. The developer step is effectively a no-op on source; its real job is the **environment remediation** so the browser-qa-agent can finally capture the travel. Do not manufacture work; do not expand scope.
- **The actual blocker is environmental (iter-15 lesson, verbatim applicable):** the DoD's `npm run build` clobbered the running `next dev` server's shared `.next/` — disk held only content-hashed PROD chunks while the dev server kept emitting HTML pointing at the unhashed dev chunk `main-app.js` → framework-chunk 404 → a dead, un-hydrated SSR shell on EVERY route. **Fix before re-verify:** stop `next dev` (by port), `rm -rf apps/frontend/.next`, restart, and never run the prod build against the served `.next`. Confirm `main-app.js` → 200 and the health badge clears before driving any UT.
- **iter-4 lesson (conversion bar):** convert J-31 `partial → passing` ONLY if the defining multi-step cross-page travel is **actually captured** — a render of one surface in isolation does not satisfy this acceptance. If browser-QA times out (exit 124) or SKIPs again, reconcile the SKIPPED/stub `ui-test-results.md` against the `*-evidence/` dir directly (inspect screenshot timestamps) before assigning a status; a tooling/environment block is a hardened re-verify, not a FAIL/ESCALATE.
- **iter-6 lesson (browser hygiene):** serialize Chrome access (one agent vacates before the other captures), de-dup evidence by sha256, and ground every "before/after" / re-point claim on **distinct** shots + a DOM/network assertion — never a single screenshot pair.
- **Strategic (forward, not this iter's fix):** even if this capture lands green and J-31 → passing (**28/31**), **GOAL_ACHIEVED is NOT autonomously reachable** — J-22/J-23/J-24 stay externally Yahoo-429 data-walled and unblock only on operator confirmation of a reachable no-key egress (J-22 auto-heals via its committed runbook) or a `docs/goal.md` scope edit. After this re-verify, expect either that operator confirmation or a correct **STALLED** on the data-walled remainder. **Do NOT autonomously retry J-22/J-23/J-24.**
