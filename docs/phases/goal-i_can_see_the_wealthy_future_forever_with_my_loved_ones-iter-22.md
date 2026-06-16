# Goal Iteration 22 — As-of stepping controls (buttons + opt-in arrows + year/month jump) and Stocks regime + theme ranking

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 22
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-79, J-80
- **Required-still-passing journeys:** J-18, J-43, J-50, J-62, J-71, J-13, J-06, J-02, J-03, J-48, J-55, J-56, J-75
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **Exactly one date selector** — the global as-of control drives every date-scoped page; `?asof` (J-43) is its SERIALIZATION, never a second state; the J-62 calendar popover is a PRESENTATION of the same one state, and any keyboard/button stepping MUST drive that SAME single state (never a second/page-local date state). *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** Partial horizons / low samples → NA + n; never synthesize a value to force a green journey.

## GOAL

The single global as-of date can be stepped with the calendar popover closed (always-visible ◀ ▶ buttons plus opt-in ← → arrow keys) and quick-jumped by year/month dropdowns, and the `/stocks` leaderboard header now shows the selected date's market-regime label + score and a ranked Top-Themes strip with `#n` chip badges — all re-displays of already-served canonical values.

## BACKGROUND

The session reached GOAL_ACHIEVED at iter-21 (75/78 buildable Must-haves green; J-22/J-23/J-24 honestly blocked-NA, non-vetoing). It is now resumed in-place: `docs/goal.md` (commit 481d8b3) queued four new Must-haves J-79..J-82, all explicitly NOT data-dependent (goal.md:2146-2152). This iteration takes the two **frontend-only, zero-backend-diff** journeys first — J-79 (as-of stepping UI) and J-80 (Stocks regime + theme-ranking re-display) — at lean depth, exactly matching iter-21's lean recommendation for an in-place resume. The remaining two are deliberately deferred: J-81 (themes/sectors forward-return columns) and J-82 (RSP NA-sort + filters + samples-validation reconciliation) touch the backend and need a full pytest gate, so they will be planned as full-depth iterations next.

Why lean: J-80 reads the EXISTING `/api/dashboard` (`regime.label`/`regime.score`, confirmed served by `snapshot_serving.py:117-118`) and `/api/themes` (theme `rank`/`score`, confirmed served by `snapshot_serving.py:191-209`) — a pure re-display, no new endpoint, no new computation, no backend file touched. J-79 extends the existing as-of components (`asof-switcher.tsx`, `asof-calendar.tsx`, `asof-provider.tsx`) — buttons + an opt-in, field-guarded global key handler + year/month dropdowns, all driving the one `setAsOf` the calendar already calls. No new Data Contract value is introduced.

Lessons applied (from session memory): (1) the J-18 "exactly one date selector" critical anti-goal is the central risk here — J-79's global key handler must drive the SAME single global as-of state and be field-guarded (never fires while focus is in input/textarea/select/contenteditable; goal.md J-79 step 5 explicitly tests caret-in-search-box). (2) `react-controlled-select-needs-native-setter` — the new Year/Month dropdowns are React-controlled `<select>`s; browser-QA must use the native-setter + bubbling change event in eval, not the Chrome MCP `select` action, then assert the live DOM. (3) J-79 supersedes the J-71 "no global window listener" constraint ONLY behind the opt-in, default-off, persisted checkbox — the panel-open `onKeyDown` (J-71) stays; the new global handler is additive and gated.

## IN SCOPE

### Backend
- [ ] None. This iteration introduces no backend change, no new endpoint, and no new stored value. (J-79 and J-80 both read already-served canonical values.)

### Frontend (if applicable)
- [ ] **J-79 — as-of stepping with the popover closed:** add always-visible **◀ / ▶** prev/next buttons in the top bar beside the as-of control (`asof-switcher.tsx`), each stepping the single global as-of to the previous / next **available snapshot date** (only among dates that actually have snapshots — never an arbitrary calendar ±1), driving the SAME `setAsOf` the calendar already calls; bounded (◀/← no-op at oldest; ▶/→ rests at Latest at newest); stays in sync with `?asof` (J-43/J-50) via the asof-provider as the sole `?asof` owner.
- [ ] **J-79 — opt-in arrow-key stepping:** a top-bar **"← → steps date"** checkbox, **persisted** and **default-off** (client-side, mirroring the existing index-chart toggle persistence pattern); when on, a **field-guarded** global key handler steps the as-of with ← / → exactly like the buttons. The handler MUST NOT fire while focus is in an `input` / `textarea` / `select` / `contenteditable`, and MUST NOT hijack scrolling when the checkbox is off. This is additive to the J-71 panel-open `onKeyDown` (unchanged).
- [ ] **J-79 — year/month quick-jump:** the calendar popover (`asof-calendar.tsx`) gains **Year** and **Month** dropdowns that navigate the **viewed month only** (a presentation aid — NOT a second date state). Selectable-day / disabled-day / "Latest" / Escape / click-to-commit affordances (J-62) unchanged.
- [ ] **J-80 — Stocks header regime label + score:** on `/stocks` (`app/stocks/page.tsx`), render the resolved as-of date's **regime label + 0–100 score** read from `/api/dashboard` (`regime.label`/`regime.score`) for the same as-of date — identical to the Dashboard (J-06), never recomputed; honest empty state if absent.
- [ ] **J-80 — Stocks header ranked Top-Themes strip + `#n` chip badges:** render a ranked Top-Themes strip (themes in descending Theme Score: `1 · …, 2 · …`) read from `/api/themes` (`rank`/`score`, same descending order the Themes page uses); a theme in the strip links to `/themes` (with `?asof` href-stamping per J-50). Add a `#n` rank badge (from the same `/api/themes` rank) on each leaderboard row's theme chips (J-56) and on the theme-filter options. Honest empty state when a date has no ranked themes.
- [ ] Both re-point with the single global as-of (J-18); leave the existing leaderboard rows, filters, symbol search (J-55), column sorting (J-48), theme chips (J-56), and forward-return columns (J-75) unchanged.

### New user-facing capability
The user can step the viewed date backward/forward one snapshot at a time without opening the calendar (buttons always; arrow keys after opting in), jump the calendar's viewed month by year/month dropdown, and — on the Stocks leaderboard — read the selected date's regime and the live theme ranking without leaving the page.

### New information displayed
On `/stocks`: the as-of date's market-regime label + 0–100 score, a ranked Top-Themes strip, and `#n` rank badges on theme chips and theme-filter options. In the top bar: ◀ ▶ stepper buttons and the "← → steps date" checkbox. In the calendar: Year + Month dropdowns.

### New user actions
◀ / ▶ prev/next as-of buttons; the "← → steps date" persisted checkbox; ← / → keys (when enabled); calendar Year + Month dropdowns; clicking a Top-Themes strip entry to open `/themes`.

### UI surface changes
Top bar (as-of switcher region), the as-of calendar popover, and the `/stocks` page header. No new page, no new nav section.

### Product surface delta
Date navigation becomes faster and non-blocking (no need to open the panel to step), and the Stocks leaderboard becomes regime- and theme-rank-aware in its header — bringing the same regime/theme context the Dashboard and Themes pages already show into the leaderboard view.

### Blueprint conformance
No new surfaces. J-79 lands on the cross-cutting top-bar as-of switcher / calendar popover (the same home as J-62/J-71). J-80 lands on **Stocks** (`/stocks`), an existing nav home. No nav-skeleton change — additive blueprint edits only.

### Data-contract additions
None. J-80 re-displays two existing Data Contract values — the **Market regime score + label** (`regime:score_regime` → `GET /api/dashboard`) and the **Theme score + rank** (`themes:score_themes` → `GET /api/themes`) — on a new surface; the blueprint's Market-regime and Theme-score rows are amended to note this `/stocks` re-display (J-80). J-79 introduces no value (the stepping/jump UI drives the existing **Resolved as-of date** single-state row). Per the no-duplicate-contract-value rule, both J-79 and J-80 read the registered canonical sources — no second computation or endpoint.

## OUT OF SCOPE

- J-81 (themes/sectors forward-return columns) — deferred to a full-depth iteration (backend read surface reusing `_leadership_returns`; needs a pytest gate for Backtest coherence).
- J-82 (RSP NA-sort + filters + Pooled default + samples-validation reconciliation) — deferred to a full-depth iteration (backend samples-validation change; needs a pytest gate).
- Any backend, API, schema, or stored-value change.
- Any change to existing leaderboard rows, scores, buckets, setups, filters, symbol search, column sort, theme chips, or forward-return columns.
- The data-walled J-22/J-23/J-24 (no fetch attempted in this frontend-only iteration).

## DEFINITION OF DONE

- [ ] Target journeys J-79 and J-80 pass via browser-qa-agent (against the committed seed, offline).
- [ ] Required-still-passing journeys (J-18, J-43, J-50, J-62, J-71, J-13, J-06, J-02, J-03, J-48, J-55, J-56, J-75) remain green — especially the **"exactly one date selector"** critical anti-goal (the stepping/jump UI drives the single global as-of, no second/page-local date state).
- [ ] No anti-goal violation introduced (no recompute on `/stocks`: regime + theme rank are re-displays of `/api/dashboard` + `/api/themes`; identical to Dashboard/Themes for the same date — J-06).
- [ ] Frontend unit/component coverage where practical (e.g. the field-guard logic and the snapshot-date bounded stepping); no regressions. Backend pytest suite unchanged (no backend diff) — a quick targeted sanity run is sufficient to confirm no inadvertent change.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys to verify by ID):**
  - **J-79:** at a historical as-of, ◀ / ▶ step to the prev/next available snapshot date with the popover closed (view never covered, page re-reads); tick "← → steps date" then ← / → step the same way (and the setting persists across reload); calendar Year/Month dropdowns jump the viewed month; at oldest ◀/← is a no-op and at latest ▶/→ rests at Latest; focus the `/stocks` symbol-search box and press ← / → — the caret moves and the as-of date does **not** change (field-guard).
  - **J-80:** `/stocks` header shows the regime label + score for the as-of date, identical to the Dashboard for that date; the ranked Top-Themes strip matches `/themes` descending order; `#n` badges appear on row theme chips and filter options; changing the global as-of re-points all three; honest empty state on a date with no ranked themes.
- **Unit/integration:** frontend logic for (a) the field-guard predicate (ignore keys while focus is in input/textarea/select/contenteditable), (b) bounded stepping among snapshot-only dates (no-op at oldest/newest), and (c) the persisted-checkbox default-off behavior, if a frontend test harness is available; otherwise documented in the handoff and covered by browser QA.
- **Error cases:** ← / → while typing in the search box must be ignored (no date change); stepping past the oldest/newest available snapshot date is a no-op (bounded); a date with no ranked themes renders an honest empty state, never a fabricated `#1` theme.

## NOTES

- This is an in-place resume after GOAL_ACHIEVED (iter-21). Evaluator recommendation was lean for an in-place resume; this iteration honors that.
- The biggest coherence risk is the J-18 "exactly one date selector" critical anti-goal. The coherence-auditor and reviewer should confirm the new buttons / arrow-key handler / year-month dropdowns all drive the SAME single global as-of state via the asof-provider's `setAsOf` (the sole `?asof` owner), and that the Year/Month dropdowns move the **viewed month only** — not a second date state. J-79 explicitly supersedes the J-71 "no global window listener" wording, but ONLY behind the opt-in, default-off, persisted checkbox; the panel-open `onKeyDown` from J-71 stays unchanged.
- J-80 coherence: `/stocks` regime + theme rank are byte re-displays — the reviewer should confirm the `/stocks` header reads `/api/dashboard` `regime.label`/`regime.score` and `/api/themes` `rank`/`score` for the resolved as-of date and asserts equality with the Dashboard/Themes values (J-06), with no client-side recompute or re-ranking.
- Browser-QA note (lessons): the new Year/Month `<select>`s are React-controlled — use the native-setter + bubbling change event in `eval`, then assert the live DOM (the Chrome MCP `select` action does not fire React onChange on this frontend). If Chrome MCP is unavailable, record SKIPPED with the link/handler code verified, per the session's established convention — do not record FAIL.
- Dev-server hygiene (lessons): never broad-kill `next dev` / `uvicorn` on this machine — kill by port only.
