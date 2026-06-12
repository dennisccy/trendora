# Goal Iteration 5 — Leaderboard sorting + href-embedded `?asof` + new-tab ticker links (J-48 / J-50 / J-54)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 5
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-48, J-50, J-54
- **Required-still-passing journeys:** J-02, J-05, J-06, J-13, J-16, J-18, J-43
- **Anti-goal reminders:**
  - **Leaderboard sorting is a view transform.** Column sorting on `/stocks` MUST re-order only the
    client-rendered rows of the already-served snapshot; it MUST NOT change, recompute, or re-rank any
    stored value — the rank `#`, scores, buckets, setup statuses, and pattern flags read exactly as
    served, and the default order remains the scanner's stored rank. Sorting MUST NOT introduce a new
    endpoint or any second compute path. *(extends Single source of truth + No recompute in the read
    path)*
  - **The `?asof` URL param is a serialization, not a second date state.** Date-scoped pages MUST reflect
    the single global as-of state in the URL while historical (and stay date-free at latest), and a URL
    carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate
    its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or
    fabricate a date. *(amends + extends Exactly one date selector)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status)
    MUST be computed exactly once by the scoring/regime engine and read identically by every page; the
    API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views.
    *(critical)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every
    date-scoped page (including Backtest) reads the single global as-of control. *(first sentences;
    full text in docs/goal.md — the import/remove date inputs on `/data` remain job parameters, never a
    date control)*

## GOAL

A user can sort the stock leaderboard by any column without disturbing a single served value, and the
selected historical as-of date now rides inside every in-app link's `href` — so middle-click, new-tab,
and copied-link navigation (including the leaderboard tickers, which now open the detail in a new tab)
all land on the exact same dated view.

## BACKGROUND

Iter-4 closed the original J-01..J-47 goal (GOAL_ACHIEVED, coherence PASS, suite 678/4/0). The human
then extended `docs/goal.md` with seven UX/perf must-haves (J-48..J-54) and re-approved the blueprint
(SESSION EXTENSION block, 2026-06-12) — `journey-history.json` carries no entries for them yet, so all
seven are effectively FAILING. This iteration takes the three pure **frontend view-transform**
journeys that share the same surfaces and compose naturally: J-50's href embedding is the mechanism
J-54's new-tab ticker links depend on ("the href carries the date per J-50"), and J-48 lives in the
same `/stocks` table. Verified current state: `app/stocks/page.tsx` does client-side **filtering only**
(its own comment: "never re-sorts"), ticker links are plain same-window `<Link>`s without `?asof`, the
sidebar hrefs are static, and no `target="_blank"` exists in the frontend. Zero backend change is
required — depth **lean**. J-49/J-51/J-52/J-53 are deferred (see OUT OF SCOPE).

Lessons applied (from `state/lessons.md` + project memory):
- **iter-1:** URL↔state sync bugs in `asof-provider.tsx` are invisible to HTTP-200 smoke tests — every
  J-50 URL leg must be asserted via **post-hydration `window.location.href`** (and here, primarily via
  the **`href` attribute in the live DOM**, which is the actual J-50 acceptance object). `npm run lint`
  is unfulfillable (ESLint not installed) — `tsc --noEmit` is the frontend gate.
- **iter-0/iter-3:** browser-qa must receive the goal.md journey text **verbatim**, capture fresh
  per-journey screenshots, and the evaluator md5-spot-checks captures for byte-identical/blank frames.
- **Memory:** the global as-of `<select>` needs a native-setter + bubbled change event to fire React
  `onChange` under Chrome MCP; J-18 is judged on "no page-local independent date state", never on
  URL date-freeness.

## IN SCOPE

### Backend
- (none — this iteration MUST NOT touch `apps/backend/`; the developer asserts a frontend-only diff
  via `git diff --stat` in the handoff)

### Frontend
- [ ] **J-48 — sortable leaderboard columns** (`apps/frontend/app/stocks/page.tsx`): make the column
  headers `Ticker`, `Sector`, `Leadership`, `Entry Quality`, `Risk`, `Setup` click-sortable with an
  asc/desc toggle and **exactly one visible sort indicator** (active column + direction); the `#`
  header restores the default order — the scanner's **stored rank** — on demand and is the initial
  state. Implement as a pure client-side, **stable** sort memo layered on the existing filter memo
  (filter + sort compose; ties keep stored-rank order). Score columns order by the stored 0–100 value
  (the A–E bucket rides along); `Setup` sorts by a deterministic order (alphabetical on the served
  status string is acceptable). No new endpoint, no new fetch, no value ever re-formatted differently.
- [ ] **J-50 — one shared as-of href helper**: add a single canonical helper (e.g. `useAsOfHref()` /
  `asofHref(path)` in `apps/frontend/lib/` or exported from `components/asof-provider.tsx`, reading the
  one global as-of state) that returns `path?asof=<D>` while historical and the clean `path` at latest.
  No component may build the param string itself — one implementation, used everywhere.
- [ ] **J-50 — apply the helper to every in-app navigational link**: `components/sidebar.tsx` (all 10
  nav entries), `app/stocks/page.tsx` (row → detail links), `app/stocks/[ticker]/page.tsx`,
  `app/scanner-runs/page.tsx` + `app/scanner-runs/[runId]/page.tsx`, `app/research/page.tsx`,
  `app/watchlist/page.tsx`, and any theme/sector member links that exist as navigational anchors. The
  `/data` date/symbol inputs are job parameters and stay untouched. Restoration on load stays exactly
  the existing J-43 path through the one global control (`asof-provider.tsx` is not expected to change;
  if it must be touched, mind the iter-1 `searchKey`-dependency lesson).
- [ ] **J-54 — leaderboard tickers open a new tab**: the `/stocks` row ticker links get
  `target="_blank"` + `rel="noopener noreferrer"`, with the href built by the J-50 helper (so the new
  tab lands on `/stocks/[ticker]?asof=D` while historical, clean at latest). This applies **only** to
  the stocks-leaderboard tickers — theme/sector member links and every other in-app link stay
  same-window (the J-52 samples tickers come with the J-51 iteration).

### New user-facing capability
Sort the stock leaderboard by any column (and restore the scanner's stored rank with one click);
middle-click / ctrl-click / copy any in-app link while viewing a historical date and land on that same
date; click a leaderboard ticker and get the stock detail in a new tab with the leaderboard's filters,
sort, scroll, and date left untouched.

### New information displayed
A visible sort indicator (active column + asc/desc) on the `/stocks` table header. No new data values —
every displayed number/badge is the already-served snapshot row.

### New user actions
- Click any of `#`, Ticker, Sector, Leadership, Entry Quality, Risk, Setup headers to sort / toggle
  direction / restore stored rank.
- Middle-click / ctrl-click / copy-link any in-app link while historical (href now carries `?asof=D`).
- Ticker click on `/stocks` now opens a new tab.

### UI surface changes
`/stocks` table header (sortable + indicator); `href` attributes of in-app links app-wide (sidebar,
leaderboard rows, scanner-runs, research, watchlist, stock-detail back-links) while historical. No new
pages, no nav changes.

### Product surface delta
The leaderboard becomes an explorable view (sort without fear — values never change), and the
historical as-of view becomes fully portable across tabs and shared links without depending on
post-navigation re-stamping. The product's "one date, one state" story now physically lives in every
link.

### Blueprint conformance
No new pages or nav sections. All work lives under the existing **Stocks** home (`/stocks`,
`/stocks/[ticker]`) and the cross-cutting top-bar/nav contract already registered in `blueprint.md`:
IA line "Stocks … J-48 sortable columns + J-54 ticker→new-tab" and the cross-cutting **J-50** entry.
Blueprint tags for J-48/J-50/J-54 flipped to "[TARGET — iter-5 in flight]" (additive edit, no
re-approval needed).

### Data-contract additions
**None.** J-48 is explicitly a view transform (blueprint invariant 13); J-50/J-54 embed the already-
registered `?asof` serialization of the single "Resolved as-of date" contract row into hrefs — no new
computed value, no new endpoint, no second way to fetch anything.

## OUT OF SCOPE

- **J-49** (dashboard indexes/regime card full-history + as-of marker) — next iteration; it touches the
  backend clamp-optional serving of `GET /api/indexes` / `GET /api/regime-history`.
- **J-51 / J-52** (research samples drill-down `/research/samples` + dated new-tab rows) — needs the new
  read-only samples endpoint family; planned after J-49.
- **J-53** (parallel multi-date backfill + per-stage timings) — concurrency-sensitive backend work;
  will be planned at **full** depth, mirroring J-46.
- Any backend change at all (including tests/config) — frontend-only diff.
- Server-side sorting, pagination/virtualization, sort-state persistence or URL-serialized sort state.
- Changing which links are same-window vs new-tab beyond the stocks-leaderboard tickers.
- The one-shot J-22/J-23/J-24 + DIA best-effort data fetch goal.md asks for "on each resume" — deferred
  to the J-53 iteration, which exercises `/data` jobs anyway (recorded here so it is not forgotten).
- Modifying `asof-provider.tsx` state semantics, the as-of switcher, or any `/data` form behavior.

## DEFINITION OF DONE

- [ ] Target journeys J-48, J-50, J-54 pass via browser-qa-agent against the goal.md journey text
  verbatim, with fresh, non-blank, per-journey evidence captures.
- [ ] Required-still-passing journeys J-02, J-05, J-06, J-13, J-16, J-18, J-43 remain green (J-02/J-16
  re-verified WITH a sort active — filter + sort compose; J-06 re-verified through the new-tab ticker
  link at a historical date; J-43's reload / fresh-tab / invalid-param legs re-verified since hrefs
  changed app-wide).
- [ ] No anti-goal violation introduced (sorting changes no served value; one helper builds every
  `?asof` href; no second date state; no new endpoint).
- [ ] `cd apps/frontend && npx tsc --noEmit` clean. The full backend pytest suite is **not** a gate for
  this iteration **iff** the diff is verifiably frontend-only (`git diff --stat` shows no
  `apps/backend/` file); if any backend file is touched, the full suite becomes required (budget
  ~35–46 min, run foreground in the dev turn or hand to the pump — never two concurrently).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-5-dev.md`,
  including the `git diff --stat` frontend-only assertion.

## TESTING REQUIREMENTS

- Browser (journeys by ID, goal.md steps verbatim):
  - **J-48**: default order = stored rank (`#` ascending); click Leadership → re-order; click again →
    direction toggles; exactly one indicator; sort by Ticker, Sector, Entry Quality, Risk, Setup in
    turn; with sort active apply Sector + Setup filters (compose); click `#` → default order returns
    and every rank/score/bucket/setup/flag value is **identical** to pre-sort (DOM-compare a sample
    row before/after).
  - **J-50**: select historical D via the native-setter technique; assert in the live DOM that the
    sidebar entries, leaderboard row links, and research/watchlist/scanner-runs links each carry
    literal `?asof=D` **in the `href` attribute** (primary evidence — middle-click itself is not
    automatable); open one copied href in a fresh tab → lands as-of D with the historical indicator,
    asserted via post-hydration `window.location.href`; switch to latest → every href is clean.
  - **J-54**: leaderboard ticker anchor has `target="_blank"` + `rel` containing `noopener`; its href
    carries `?asof=D` while historical and is clean at latest; opening it lands on the dated detail
    with scores identical to the leaderboard row (J-06); the originating tab's filters + sort + date
    are undisturbed afterwards.
  - Re-verify required-still-passing set per DEFINITION OF DONE.
- Unit/integration: none required beyond `tsc --noEmit` (no backend change; frontend has no test
  runner — do not write a lint DoD, ESLint is not installed).
- Error cases: invalid `?asof` in a deep link still degrades to the latest view (J-43 leg);
  sorting handles ties stably (equal scores keep stored-rank order) and never throws on the
  empty-state (zero filtered rows).

## NOTES

- Prior verdict was GOAL_ACHIEVED for the original journey set; this is the first iteration of the
  human-approved J-48..J-54 extension batch (blueprint SESSION EXTENSION block already registered and
  re-approved — `blueprint.approved` present, no reapproval pending).
- Remaining batch plan (for the evaluator's recommendation context, not binding): iter-6 → J-49
  (lean, clamp-optional serving + marker), iter-7 → J-51+J-52 (samples endpoint family + page,
  count-coherence contract), iter-8 → J-53 at **full** depth (concurrency) + the one-shot best-effort
  data fetch.
- Implementation hint, not mandate: the existing filter memo in `app/stocks/page.tsx` already comments
  "never re-sorts" — extend that comment chain so the single-source-of-truth intent stays legible to
  the reviewer and coherence-auditor.
- QA budget note: no `/data` jobs and no backend restarts are needed this iteration; do not restart
  the backend on :8835 (project memory), and never broad-`pkill` dev servers — kill by port only if a
  frontend restart is required.
