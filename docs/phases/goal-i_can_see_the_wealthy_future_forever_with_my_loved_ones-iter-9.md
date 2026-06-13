# Goal Iteration 9 — Stocks symbol search + Theme column/filter + expandable theme members (J-55 / J-56 / J-57)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 9
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-55, J-56, J-57
- **Required-still-passing journeys:** J-02, J-03, J-05, J-06, J-16, J-48, J-50, J-54
- **Anti-goal reminders:**
  - **Leaderboard sorting, searching, and table filtering are view transforms.** Column sorting on
    `/stocks` (and on the `/research/samples` table — J-64), the J-55 symbol search, the J-56 theme
    filter, and the J-64 ticker filter MUST re-order or narrow only the client-rendered rows of the
    already-served payload; they MUST NOT change, recompute, or re-rank any stored value — the rank `#`,
    scores, buckets, setup statuses, pattern flags, and theme membership read exactly as served, and the
    default order remains the scanner's stored rank. A filtered view MUST stay honest about what it
    hides ("x of N") and MUST NOT alter a published cohort total. Sorting/searching/filtering MUST NOT
    introduce a new endpoint or any second compute path. *(extends Single source of truth + No recompute
    in the read path)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status)
    MUST be computed exactly once by the scoring/regime engine and read identically by every page; the
    API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views.
    *(critical)*
  - **The `?asof` URL param is a serialization, not a second date state.** Date-scoped pages MUST reflect
    the single global as-of state in the URL while historical (and stay date-free at latest), and a URL
    carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate
    its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or
    fabricate a date. *(amends + extends Exactly one date selector)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/
    unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(here: a
    no-match search/filter result renders the existing honest empty state — never a fabricated row)*

## GOAL

A user can find any stock on the leaderboard by typing its ticker or company name, see and filter by
each row's theme membership right on `/stocks`, and expand a theme's full member list on `/themes` —
with every member ticker opening the dated stock detail in a new tab.

## BACKGROUND

Iter-8 closed the J-48..J-54 extension (GOAL_ACHIEVED, 51 buildable journeys green, zero regressions,
coherence WARN-advisory-only). The human then extended `docs/goal.md` with THIRTEEN new must-haves
J-55..J-67 (commit a5d8b5c) and resumed this session in place — the exact precedent of the 2026-06-12
J-48..J-54 resume. `journey-history.json` carries no entries for J-55..J-67 yet, so all thirteen are
effectively FAILING. goal.md states explicitly: **"J-55 … J-67 are NOT data-dependent"** — none may be
recorded blocked-NA for provider reasons.

This iteration takes the three pure **frontend view-transform** journeys that need zero backend or
config change (verified against the current code, not assumed):

- `apps/frontend/lib/api.ts` `StockRow` (line ~235) already serves `ticker`, `name` (company name),
  and `themes: ThemeChip[]` on every leaderboard row — J-55's search vocabulary and J-56's Theme
  column are pure re-displays of already-served fields.
- `apps/frontend/app/stocks/page.tsx` already implements the init-once-from-URL / reflect-on-change
  filter-param pattern (`sector`/`setup`/`pattern`) and the filter-THEN-sort memo (J-48) — J-55's
  `?q=` and J-56's `?theme=` slot into the same proven mechanism.
- `apps/frontend/app/themes/page.tsx` truncates members via `row.members.slice(0, 6)` with a
  non-expandable `+n` remainder — J-57 makes that an expand/collapse and turns member tickers into
  dated new-tab links via the existing `useAsOfHref` helper (J-50 mechanics, proven iters 5–7).

Zero backend diff required ⇒ depth **lean**; the frontend gate is `tsc --noEmit` (ESLint is not
installed — iter-1 lesson). J-58 (sectors names/members) needs new config reference data + backend
serving and is deferred; the jobs journeys (J-59/J-60/J-66/J-67) are full-depth backend work, deferred.

Lessons applied (from `state/lessons.md` + project memory):
- **iter-5 (nested interactive elements):** wrapping labels/cells in clickable affordances around
  `TermInfo`/`InfoTooltip` — or placing links inside a `role="button"` row — nests interactive
  elements (invalid DOM, dev-overlay "1 error" badge, click bubbling into the row toggle). The J-56
  theme-chip `+n` overflow, the J-57 expand/collapse control, and the J-57 member links MUST be
  siblings of (or outside) any clickable row/button, with `stopPropagation` where they live inside a
  clickable `<tr>`; QA must assert NO dev-overlay error badge and that activating a member link or
  `+n` never toggles the row.
- **iter-1 (URL↔state sync):** assert `?q=`/`?theme=` serialization via **post-hydration
  `window.location.href`** and link `href` attributes in the live DOM, never navigation-time URLs or
  HTTP-200 smokes. Init-once from the URL, reflect on change, omit when empty — never driven FROM
  `searchParams` (no state↔URL loop; the stocks page documents this pattern in code).
- **iter-0/iter-7 (evidence hygiene):** browser-qa receives the goal.md journey text **verbatim**,
  captures one fresh PNG per claimed surface (no byte-identical reuse — md5 the evidence dir), and
  the evaluator grades against goal.md acceptance, never the QA table.
- **project memory (React controlled select):** Chrome MCP `select` does not fire React `onChange`
  on this frontend — QA drives the new Theme filter via the native-setter + bubbled change event,
  then asserts the live DOM.

## IN SCOPE

### Backend
- (none — this iteration MUST NOT touch `apps/backend/`; `git diff --name-only -- apps/backend/`
  must be empty, as the iter-5 precedent proved for its frontend-only diff)

### Frontend
- [ ] **J-55 — `/stocks` type-to-filter symbol search:** a search input alongside the existing
      Sector/Setup/Pattern filters; case-insensitive substring match on `row.ticker` AND `row.name`,
      applied per keystroke (no submit affordance, no Enter, no refetch — the `[asOf]`-keyed fetch is
      untouched); composes filter-THEN-sort with the existing filters, the new J-56 theme filter, and
      J-48 sorting; serializes as `?q=` exactly like the existing filter params (init-once from URL,
      reflected on change, omitted when empty, never a date — J-18); honest `x / N` visible count;
      no-match renders the existing honest empty state.
- [ ] **J-56 — `/stocks` Theme column + theme filter:** a Theme column re-displaying each row's
      already-served `themes` chips verbatim (same config-derived membership the detail page shows —
      J-06); a row in many themes shows a compact chip list with a `+n` overflow whose full membership
      is readable in place (tooltip or expand — never a nested interactive element inside another
      control); a Theme filter whose vocabulary derives from the served rows' themes in config order
      (like the Sector filter derives from rows), keeping exactly the rows whose membership contains
      the selection; serializes as `?theme=`; an unrecognized `?theme=` value never crashes and
      fabricates no filter (mirror `parsePatternParam`'s graceful handling); composes with every
      existing filter, the J-55 search, and J-48 sorting.
- [ ] **J-57 — `/themes` expandable members + dated new-tab links:** the `+n` placeholder becomes a
      working expand/collapse revealing EVERY remaining member (re-display of the already-served
      member list — nothing refetched); every member ticker renders as a link to `/stocks/[ticker]`
      opening in a new tab (`target="_blank"` + `rel="noopener noreferrer"`), the href embedding the
      global `?asof` while historical and clean at latest (via the existing `useAsOfHref` helper —
      J-50); the originating tab's expansion state, scroll, and selected date are never disturbed;
      activating a member link or the `+n` control never toggles the theme row (`stopPropagation`).

### New user-facing capability
Find any leaderboard stock instantly by ticker or company name; slice the leaderboard by theme;
read every theme's complete member list and jump to any member's dated detail without losing your
place.

### New information displayed
- Theme membership chips per row on `/stocks` (previously only on the detail page — same served value)
- The full member list of every theme on `/themes` (previously truncated at 6 with a dead `+n`)
- Honest `x / N` visible-row count on `/stocks` while a search/filter narrows the view

### New user actions
- Type-to-filter search input on `/stocks` (no button)
- Theme filter select on `/stocks`
- `+n` expand/collapse control per theme row on `/themes`
- Member-ticker links on `/themes` (new tab, dated)

### UI surface changes
- `/stocks`: one new input, one new filter select, one new table column; existing columns/filters/sort
  untouched
- `/themes`: expanded member panel gains full-list expand/collapse + linkified tickers

### Product surface delta
The leaderboard becomes findable and theme-aware (the goal.md "findable and theme-aware" success
criterion); member structure on `/themes` becomes fully legible with dated drill-through — no
behavioral change anywhere else.

### Blueprint conformance
No new pages or routes. All work lives on the existing **Stocks** (`/stocks`) and **Themes**
(`/themes`) homes in the approved Information Architecture. Blueprint nav annotations updated
additively (no nav-skeleton change — no re-approval needed).

### Data-contract additions
**None.** J-55/J-56/J-57 are pure client-side view transforms over values already registered in the
Data Contract (stock rows incl. `name` + `themes` from `scoring:score_stocks` via `GET /api/stocks`;
theme members from `themes:score_themes` via `GET /api/themes`). No new endpoint, no new computed
value, no second compute path — reading the registered canonical sources only.

## OUT OF SCOPE

- **J-58** (sectors ETF names/descriptions + universe members) — needs new config reference data
  (industry catalog + stock→industry mapping) and backend serving; next UI-cluster iteration.
- **J-64 / J-65** (samples table sort/filter + `N=` chips new-tab) — same view-transform contract,
  different surface; bundled together in a later lean iteration.
- **J-61 / J-62** (availability heatmap endpoint + as-of calendar popover) — J-61 adds a read-only
  backend endpoint; deferred.
- **J-63** (event-study episodes default) — backend research-module change; deferred.
- **J-59 / J-60 / J-66 / J-67** (stage-aware resume, run-history-from-start, fine-grained progress,
  parallel-backfill session soundness) — concurrency-sensitive backend work; FULL-depth iterations
  per the J-46/J-53 precedent.
- Backend pre-computation of `speedup_factor` (iter-8 coherence-WARN residual tidy) — fold into the
  first iteration that touches `data_manager.py`/`data/page.tsx` job-card code (likely J-66).
- Any change to `apps/backend/`, `config.yaml`, the sort logic, the served row shape, or the
  `asof-provider` state semantics.

## DEFINITION OF DONE

- [ ] Target journeys J-55, J-56, J-57 pass via browser-qa-agent against the goal.md steps verbatim
- [ ] Required-still-passing journeys J-02, J-03, J-05, J-06, J-16, J-48, J-50, J-54 remain green
- [ ] No anti-goal violation introduced (view-transform contract: every served value reads exactly as
      served; no new endpoint; `?q=`/`?theme=` are never a date state)
- [ ] `git diff --name-only -- apps/backend/` is empty (frontend-only contract; backend suite not
      re-gated — if ANY backend file is touched, the full pytest suite (~35–46 min, hand to the pump)
      becomes a gate per session precedent)
- [ ] `cd apps/frontend && npx tsc --noEmit` clean (the frontend gate; `npm run lint` is unfulfillable)
- [ ] No Next dev-overlay error badge on any captured page (iter-5 regression signal)
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-9-dev.md`

## TESTING REQUIREMENTS

- Browser (journey text verbatim from docs/goal.md; one fresh capture per claimed surface, md5-unique):
  - **J-55:** type `nv` → rows narrow per keystroke to ticker/name substring matches (NVDA matches);
    search + Sector filter + J-48 header sort compose (searched+filtered rows in sorted order); clear
    restores all rows with filters/sort untouched; reload with `?q=nv` restores the search
    (post-hydration `window.location.href` + DOM row-count assertions); a no-match string renders the
    honest empty state.
  - **J-56:** Theme column chips render per row; a many-theme row's `+n` overflow is readable in
    place; theme filter keeps only member rows; composes with Sector/Setup/Pattern + J-55 search +
    J-48 sort; empty result → honest empty state; open a filtered row's detail — its theme chips match
    the leaderboard exactly (J-06 leg); `?theme=` serializes/restores; unrecognized `?theme=` value
    degrades gracefully (no crash, no fabricated filter). Drive the select via native setter + bubbled
    change event (project memory).
  - **J-57:** expand a >6-member theme, activate `+n` → ALL members render in place; collapse works;
    member click opens detail in a new tab (assert `target`/`rel`/`href` on the live DOM) while the
    themes tab keeps expansion + scroll + date; at historical D the member `href` itself carries
    `?asof=D` and the new tab lands on D through the one global control; at latest the hrefs are
    clean; clicking a member link or `+n` never toggles the row.
  - Required-still-passing: J-02 (sector+setup filters with search active), J-03 (ranked themes
    board intact), J-05/J-06 (NVDA detail + numeric score identity leaderboard↔detail), J-16 (VCP
    filter composes with search — honest empty state), J-48 (default order = stored rank; `#`
    restores; one aria-sort indicator), J-50/J-54 (historical href stamping + leaderboard ticker
    new-tab unchanged).
  - Opportunistic (non-gating, carried since iter-2): the J-44 toggle off → reload → still-off cycle —
    capture it EARLY in the browser session (iter-6 lesson).
- Unit/integration: no backend tests required (no backend diff). Frontend: `tsc --noEmit` clean.
- Error cases: no-match `?q=` → honest empty state (never a fabricated row); unrecognized `?theme=` →
  graceful no-crash degradation; a theme with ≤ preview-limit members shows no `+n` control; empty
  search string omits `?q=` from the URL.

## NOTES

- **Evaluator bookkeeping:** create first `journey-history.json` entries for J-55..J-67 this
  iteration — the three targets per evidence, the other ten as `failing` (not yet built). None of the
  thirteen may be recorded blocked-NA (goal.md: "J-55 … J-67 are NOT data-dependent").
- **Recommended sequencing for the remainder** (decomposer's working plan, evaluator may amend):
  iter-10 lean → J-64 + J-65 (samples sort/filter + chips new-tab); iter-11 lean → J-58 (config
  industry catalog + members; backend/config touch ⇒ full pytest gate); iter-12 lean → J-62 calendar
  popover (+ J-61 heatmap if it fits — read-only endpoint); iter-13 lean → J-63 episodes;
  iter-14 FULL → J-59 + J-60 (stage-aware resume + run-history lifecycle); iter-15 FULL → J-66 + J-67
  (fine-grained progress incl. the 318/159 fix + 'committed'-session crash fix).
- Iter-8 coherence verdict was COHERENCE-WARN (advisory only — the frontend `speedupFactor` display
  division); this iteration does not touch that surface, the tidy is queued under J-66.
- Blueprint updated additively this iteration: SESSION EXTENSION (2026-06-13) comment block for
  J-55..J-67, nav annotations on existing homes, invariant 13 extended to name the new view
  transforms. No nav-skeleton change — no `blueprint.reapproval-requested` written.
