# Goal Iteration 8 — Snapshot-served reads + global as-of date switcher (J-15, J-13)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-15, J-13
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. *(extends Single source of truth)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.

## GOAL

Let the user browse the whole dashboard (Dashboard, Stocks, Themes, Sectors, Stock Detail) **as of any past trading day** via a global top-bar date switcher with a clear "viewing as-of D (historical)" indicator, while re-pointing those read endpoints to **serve canonical values from the persisted immutable snapshot for the resolved date** (computed once, then read from storage) instead of recomputing per request.

## BACKGROUND

The goal was re-opened: iter-7 reached **GOAL_ACHIEVED** for the original 11 Must-have journeys (J-01…J-11, all `passing`), then commit `ed7712b` expanded `docs/goal.md` with **five new Must-have journeys** — J-12 (glossary), J-13 (global as-of switcher), J-14 (backtest scorecard), J-15 (snapshot-served reads), J-16 (VCP) — plus capabilities 16–19 and new anti-goals. This iteration starts the new round with the **foundational keystone J-15 + J-13** because: (a) the live read endpoints currently **compute on-request** (`dashboard.py` calls `score_regime`/`score_stocks` live with `latest_data_date`, no `as_of` param) so both journeys are unbuilt; (b) J-14 (Backtest) depends on as-of snapshot reads; and (c) "snapshot-served reads" and "the as-of-resolved read path" are the *same* mechanism (resolve as-of → load-or-create-once the immutable snapshot → serve stored rows), so building them together avoids touching the critical read path twice. The snapshot infrastructure already exists (`app.engine.scanner:run_scan`, the append-only `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores` tables, and `GET /api/runs` + `/api/runs/{run_id}` from iter-5/6) — this iteration **re-points the live-view endpoints to use it**, completing the architecture the blueprint always intended (its iter-5/6 notes explicitly left the live endpoints on on-request compute, "NOT re-pointed"). Depth is **full**: it crosses backend + frontend, changes the core read path of 5+ endpoints, exercises on-demand snapshot creation, needs new unit tests beyond browser smoke, and carries real regression risk to 11 passing journeys.

## IN SCOPE

### Backend
- [ ] Add an **as-of resolution helper** (in `app.engine.scanner`, or a small dedicated helper that calls into it) that maps an optional `as_of` date → the **stored** immutable snapshot for that date: return the existing `scanner_runs` row + its result/score rows if present; otherwise **create it exactly once** via the canonical `app.engine.scanner:run_scan(asof=D)` (INSERT-only into the append-only snapshot tables; bars with **date ≤ D** only). Default `as_of` = the latest stored `scanner_runs.asof_date`.
- [ ] **Re-point** these read endpoints to serve canonical values from the **resolved stored snapshot rows** (regime score+label+breadth, the three per-stock scores + A–E bucket + setup status + reason + invalidation + theme membership, sector scores, theme scores, candidate counts) — **never** from a live `score_regime`/`score_stocks`/`score_sectors`/`score_themes` call:
  - `GET /api/dashboard`
  - `GET /api/stocks` (list)
  - `GET /api/stocks/{ticker}` (detail)
  - `GET /api/sectors`
  - `GET /api/themes`
- [ ] Each re-pointed endpoint accepts `?as_of=YYYY-MM-DD` and **echoes the resolved `asof_date`** it actually served in its payload (so the UI can render the historical indicator and confirm coherence). `/api/dashboard` already returns `asof_date`; add it to the others.
- [ ] `GET /api/stocks/{ticker}/bars` accepts `?as_of=YYYY-MM-DD` and returns OHLCV bars + the server MA series with **date ≤ D** (no-lookahead) for the as-of chart. (Raw bars are not a recomputed score, so snapshot storage is **not** required for this endpoint — only the as-of slice + no-lookahead.)
- [ ] Reject an **invalid as-of** explicitly (no fabrication): a future date / a date with no bars ≤ D / an unparseable date → an explicit 4xx (e.g. 400/404/422), never a synthesized snapshot.
- [ ] Keep `GET /api/watchlist` current Leadership/Entry/Risk + bucket + setup + invalidation reading the canonical **latest-snapshot** stock row (the SAME row `/api/stocks` serves at latest) so the single-source-on-a-write-surface (J-06) and J-11 stay green — no second source, no stored-then-drifting copy.

### Frontend
- [ ] Add a **global top-bar as-of date switcher** in the app shell/layout, present on the as-of-aware pages. Its date options come from the canonical `GET /api/runs` (the immutable run list); default selection = latest.
- [ ] Selecting a date **re-points** Dashboard (`/`), Stocks (`/stocks`), Themes (`/themes`), Sectors (`/sectors`), and Stock Detail (`/stocks/[ticker]`) to that date by passing `as_of` to their data fetches. Switching back to latest restores the current/default view.
- [ ] Render a clear **"viewing as-of D (historical)"** indicator whenever the resolved date ≠ latest (e.g. a top-bar banner/badge using the `--warn` design token), and a normal/"latest" state otherwise.
- [ ] The frontend **only re-formats** server values — it MUST NOT recompute any score/bucket/return; the as-of state only changes which date's stored values are fetched and how the indicator reads.

### New user-facing capability
The user can time-travel the whole primary dashboard — pick any past trading day from a global switcher and see Dashboard, Stocks, Themes, Sectors, and Stock Detail exactly as the scanner recorded them on that date, clearly labelled historical — and pages now render from persisted immutable snapshots (served from storage, not recomputed per request).

### New information displayed
- The resolved as-of date on each page; a "viewing as-of D (historical)" indicator; the switcher's list of available dates (from `GET /api/runs`).
- All score/regime/sector/theme/setup values are unchanged in meaning — now sourced from the stored snapshot for the resolved date rather than recomputed live.

### New user actions
- The global top-bar as-of date switcher: select a past date; reset to latest.

### UI surface changes
- A new global top-bar control + historical indicator across the as-of-aware pages. **No new page/route, no sidebar change.**

### Product surface delta
- Every primary page becomes time-travelable, and the product visibly serves from immutable snapshots and labels historical views honestly — making the as-of evidence in Scanner Runs (J-08) reachable from the everyday pages too.

### Blueprint conformance
- All target pages already exist under the established Information Architecture (Dashboard / Stocks / Themes / Sectors, plus row-reached Stock Detail under Stocks). The as-of switcher is an **additive global top-bar control** — registered in `blueprint.md` this iteration with **no nav-skeleton change and no `blueprint.reapproval-requested`** (it adds no sidebar section and moves no feature home).

### Data-contract additions
- **No new computed value.** Registered additively in `blueprint.md`: a "Resolved as-of date + available as-of dates" row — available dates are served by the **existing** canonical `GET /api/runs`; the resolved `asof_date` is echoed by each re-pointed read endpoint. The read endpoints are re-pointed to serve **existing** Data-Contract values from the persisted snapshot for the resolved as-of date (a serving-model change, recorded as the iter-8 serving note). **No value is computed by a second path** — `run_scan` remains the one place each canonical engine runs, and the endpoints serve its stored output.

## OUT OF SCOPE

- **J-12** (`/methodology` glossary + inline tooltips), **J-14** (`/backtest` Time-Machine + per-date forward-test scorecard), and **J-16** (VCP detection / leaderboard filter / badge / VCP-vs-non-VCP breakdown) — each is a later iteration (J-14 and J-12 will add new nav entries and so will need `blueprint.reapproval-requested` then).
- Any new score, indicator, forward-return, or aggregate computation.
- Re-pointing or otherwise changing `GET /api/runs`, `GET /api/runs/{run_id}`, or `GET /api/system-health`.
- Live-provider / network fetch — offline committed seed only.
- A full free-form calendar that resolves arbitrary non-seed dates in the UI: the switcher offers the stored run dates from `/api/runs` (which always resolve instantly); the backend's create-once path for any seed trading day is exercised by unit/integration tests, not necessarily by a calendar widget.
- APScheduler / live scheduled scans (the create-once-on-first-view path is sufficient here).

## DEFINITION OF DONE

- [ ] Target journeys **J-15** and **J-13** pass via browser-qa-agent (with distinct, hash-checked evidence per journey).
- [ ] Required-still-passing journeys **J-01…J-11 remain green** — special attention to **J-06** (leaderboard score == detail score, now both from the stored row), **J-07** (a Risk-Off run still shows zero Actionable), **J-08** (immutable run history unchanged), and **J-11** (watchlist current values still equal `/api/stocks` latest).
- [ ] No anti-goal violation introduced — in particular the criticals: no-lookahead, snapshots-immutable, single-source, **No recompute in the read path**, **On-demand snapshots stay immutable & lookahead-free**, and Risk-Off-gates-Actionable.
- [ ] Unit/integration tests pass (see TESTING REQUIREMENTS); no regressions in the existing suite (179+ tests per iter-7).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-dev.md`.
- [ ] Audit handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-audit.md` (full-depth pipeline; this has been chronically missing — see NOTES).

## TESTING REQUIREMENTS

- **Browser (Chrome MCP):**
  - **J-15** — load `/stocks` for the latest date, reload, then load `/`, `/themes`, `/sectors`; confirm rows render from the stored snapshot (not a per-request recompute), the warm load is fast (< ~1.5 s), and a stock's three scores are identical to its Stock Detail page (coherence preserved).
  - **J-13** — on `/`, open the as-of switcher, select a past trading day; confirm `/`, then `/stocks`, `/themes`, `/sectors` all reflect that date and the values match that date's Scanner Run (not the latest); confirm a clear "viewing as-of D (historical)" indicator is visible; switch back to latest and confirm the current view is restored.
  - **Regression smoke** — J-01 (dashboard panels render), J-02 (leaderboard filters still work), J-06 (NVDA list == detail), J-07 (open the Risk-Off run → zero Actionable).
- **Unit/integration (backend):**
  - As-of **resolver**: a given `as_of` resolves to the correct stored snapshot; default resolves to the latest stored run date; the resolved `asof_date` is echoed.
  - **Create-once / immutability**: viewing a not-yet-stored seed date creates the snapshot once; a **second** view of the same date reads the existing rows and performs **no UPDATE and creates no duplicate** snapshot/result rows (assert row counts + identity).
  - **No-lookahead** on on-demand creation: an as-of-D snapshot uses only bars with date ≤ D (no future bar influences any stored as-of score) — extend/reuse the existing walk-forward no-lookahead guard.
  - **Snapshot-served coherence**: the re-pointed `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) return **byte-identical** canonical fields from the same stored row (J-06); the iter-5 faithful-equality guarantee (latest stored snapshot == live computation) still holds.
  - **Watchlist coherence**: `/api/watchlist` current scores/bucket/setup/invalidation still equal `/api/stocks` at latest.
  - **No-recompute assertion**: the re-pointed read endpoints serve stored values without invoking the live scoring/regime engines for an already-persisted date (e.g. via a spy/seam or by asserting served values equal the stored snapshot rows, not a fresh computation).
- **Error cases:** future `as_of` → explicit 4xx; a date with no bars ≤ D → explicit 4xx; an unparseable `as_of` → explicit 4xx; never fabricate a snapshot or a score to satisfy a bad date.

## NOTES

- **Why these two journeys together (not split):** the snapshot-served read path *is* the as-of-resolved read path. Implementing J-15 alone (latest-only, served-from-storage) would force re-touching the same critical endpoints again for J-13's `as_of` param. Doing the as-of-resolved, snapshot-served read path once delivers both and halves the regression risk to J-01–J-06. This matches the session's established rhythm of two coupled journeys per full iteration (iter-5 = J-07+J-08, iter-6 = J-09+J-10).
- **Lessons applied (episodic memory):**
  - *(iter-2 lesson — read canonical, never recompute when a new code path touches a contract value):* the re-pointed endpoints MUST read the stored snapshot row produced by the one `run_scan`; they MUST NOT introduce a second computation of any score/bucket/return. This is the exact single-source drift the coherence-auditor will FAIL.
  - *(iter-1 lesson — no-lookahead / offline determinism):* on-demand snapshot creation for a past date MUST use only bars ≤ D, against the frozen offline seed (no live fetch mid-loop, which would make the as-of values irreproducible).
  - *(iter-6 lesson — distinct evidence):* J-13 needs **distinct** per-journey screenshots (a historical view on ≥2 different pages + the historical indicator + the back-to-latest restore); md5/diff the PNGs so a shared full-page capture is not counted as multiple proofs.
- **Standing harness gaps (runner-script scope — NOT product; do not attempt to fix via this spec, which has proven ineffective across iters 3–7):** the dedicated browser-qa has SKIPPED on an HTTP-000/CORS flap for **7 consecutive iterations**, and the audit handoff has been missing for 7 full-depth iterations. For THIS UI-heavy iteration, if browser-qa SKIPs, the evaluator should reconcile from on-disk evidence and, if needed, boot the services directly and produce live evidence — launching the backend with `CORS_ORIGINS=http://localhost:<frontend-port>` and a frontend rebuilt with `NEXT_PUBLIC_API_URL=http://localhost:8835` (iter-7 root-cause lesson: a backend without `CORS_ORIGINS` defaults to `:3000` and silently blocks `:3835`/`:3836`, rendering the honest "Backend unavailable" card even though `curl` succeeds). When awaiting UI text, await a value unique to the historical state (e.g. the as-of date string or the "(historical)" indicator), not text that also appears in a placeholder.
- **Regression watch:** this is the first iteration that changes the **read path** of journeys that have been green since early iters. The highest-risk regressions are J-06 (both views must read the SAME stored row), J-11 (watchlist current values must stay equal to `/api/stocks` latest), and the criticals (immutability of on-demand snapshots, no-lookahead). The DoD requires these to be re-proven, not assumed.
- **After iter-8:** the remaining new Must-haves are J-14 (Backtest scorecard — builds on this as-of snapshot read path + the existing forward-testing engine), J-16 (VCP — config-driven detected-pattern flag riding the snapshot row + leaderboard filter + System Health breakdown), and J-12 (config-backed glossary + inline tooltips, which should include the VCP catalog entry, so it pairs naturally after J-16).
