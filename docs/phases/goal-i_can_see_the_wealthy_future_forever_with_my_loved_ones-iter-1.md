# Goal Iteration 1 — ISO dates everywhere (J-42) + deep-linkable ?asof (J-43)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-42, J-43
- **Required-still-passing journeys:** J-06, J-13, J-17, J-18, J-20
- **Anti-goal reminders** (verbatim from `docs/goal.md` — the ones this iteration can violate; ALL anti-goals still apply):
  - **One date format, displayed — ISO contracts unchanged.** Every user-facing calendar date MUST render `yyyy-MM-dd` through one shared formatter/constant (no locale-dependent widget output, no per-component format literals); date inputs MUST validate the exact format before submit; API parameters, DB values, and config dates remain ISO and MUST NOT change shape. *(extends No magic numbers)*
  - **The `?asof` URL param is a serialization, not a second date state.** Date-scoped pages MUST reflect the single global as-of state in the URL while historical (and stay date-free at latest), and a URL carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or fabricate a date. *(amends + extends Exactly one date selector)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. … The `?asof` URL query param (J-43) is the **serialization of that single global state** — written by and restored through the one global control — NOT a second date state; no page parses or holds its own. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*

## GOAL

After this iteration, every user-facing calendar date in Trendora reads `yyyy-MM-dd` regardless of browser locale (with validated ISO text inputs on `/data`), and a selected historical as-of date survives click-through, reload, and new tabs via a `?asof=yyyy-MM-dd` URL serialization of the one global control.

## BACKGROUND

Baseline (iter-0) confirmed J-01..J-41 already passing on unchanged code; the real gap is J-42..J-47. The evaluator recommended starting with J-42 + J-43 together: both are frontend date-state work on the same surfaces (`components/asof-provider.tsx`, a new shared date formatter, `/data` date inputs), and J-43's URL serialization is what J-44/J-45's QA will navigate with next iteration. J-42 is currently **partial** — displayed dates are ISO (backend sends ISO strings rendered raw) but `apps/frontend/app/data/page.tsx` still uses four native `type="date"` inputs (locale-rendered widgets, lines ~925/935 fetch form and ~1684/1694 remove form) and no shared formatter exists. J-43 is **failing** — `components/asof-provider.tsx` has zero `?asof` read/write handling; loading `/stocks?asof=2026-05-01` leaves the switcher at "Latest".

**Lessons applied (from `lessons.md` iter-0 + evaluator caution):** (a) J-42's acceptance includes validated ISO TEXT inputs and ONE shared formatter — ISO-looking output alone was already rejected as an overclaim; (b) the full backend pytest suite was skipped at baseline (collect-only) — this iteration's gate MUST run it once; (c) browser-QA must take journey text **verbatim from docs/goal.md** and capture fresh, journey-specific screenshots — iter-0's QA invented journey definitions for ~20 IDs and recycled byte-identical evidence.

Both target journeys are already registered as approved [TARGET] rows in the session blueprint's Data Contract ("Resolved as-of date … J-43 [TARGET]" and "J-42 [TARGET] — Displayed date format") — this iteration builds exactly to those rows; no blueprint edit and no nav change is needed.

## IN SCOPE

### Backend
- [ ] No backend code changes. (API parameters, DB values, and config dates already ISO — they MUST NOT change shape.)
- [ ] Run the full backend pytest suite once as part of this iteration's gate (closes the baseline DoD gap; last authoritative green run was 621 passed / 4 skipped / 0 failed at the same product commit). NOTE: the full suite takes ~14 minutes (heavy walk-forward boot) — never run two pytest invocations concurrently.

### Frontend
- [ ] **Shared date formatter (J-42):** create `apps/frontend/lib/dates.ts` exporting the single ISO date-format constant + a `formatIsoDate()` formatter (and the exact-format validator used by inputs). Every surface that displays a calendar date renders through it — no per-component date-format literals, no locale-dependent widget output. Sweep: the as-of switcher options + "viewing as-of … (historical)" indicator, run lists (`/scanner-runs`), watchlist date-added, Data Manager job cards / coverage figures / missing-data diagnostic rows, and chart tooltip/crosshair dates (`components/price-chart.tsx`). Where backend ISO strings are already rendered raw, route them through (or document them as pass-through of) the shared constant so one module is the format authority. Compact chart **axis tick labels** may stay abbreviated (scale marks, not displayed dates — per J-42 acceptance).
- [ ] **Validated ISO text inputs on `/data` (J-42):** replace the four native `type="date"` inputs in `apps/frontend/app/data/page.tsx` (fetch/backfill start+end, remove-data start+end) with validated ISO **text** inputs: exact `yyyy-MM-dd` format check + calendar validity (reject `2026-13-40` and `10/06/2026`), visible inline error state, submit blocked while invalid; the submitted job uses exactly the typed dates. These inputs remain **job parameters, not the global as-of control** — the `?asof` work must not touch them.
- [ ] **`?asof` URL serialization (J-43):** extend `components/asof-provider.tsx` (and/or the app-shell wiring around it) so the single global as-of state is serialized to `?asof=yyyy-MM-dd` in the URL of date-scoped pages whenever a historical date is selected, and the URL is date-free at latest. On load, a URL carrying `?asof` restores that date **into the one global control** (the top-bar switcher reflects it). An unknown/invalid `?asof` (malformed string or a date not in the run list) degrades safely to the latest view — no crash, no fabricated date. Client-side navigation (leaderboard row → `/stocks/[ticker]`), reload, and a fresh tab all preserve the date. The URL is the serialization of the ONE state — no page parses or holds its own date state, and the provider remains the only reader/writer of the param.

### New user-facing capability
A historical as-of view is now shareable and durable: copy the URL, reload, open a new tab, or click through leaderboard→detail and the exact historical date is restored through the global switcher. Date entry on `/data` is locale-proof: type exact `yyyy-MM-dd` with immediate validation feedback.

### New information displayed
Every displayed calendar date is guaranteed `yyyy-MM-dd` regardless of browser locale (including chart tooltip/crosshair dates); `/data` date fields show a visible inline validation error on invalid input.

### New user actions
- Type ISO dates directly into the `/data` fetch/backfill and remove-data forms (validated text inputs replacing the native pickers).
- Paste/share a deep link carrying `?asof=yyyy-MM-dd` to open any page at that historical date.

### UI surface changes
- `/data` — four date fields become validated ISO text inputs with error states.
- URL bar on every date-scoped page — carries `?asof=yyyy-MM-dd` while historical; date-free at latest.
- Chart tooltips/crosshairs and any remaining date renders — formatted through the shared formatter (visually unchanged where already ISO).
- No new pages, no nav change, no layout change.

### Product surface delta
No new surface; two cross-cutting contracts (uniform ISO date presentation; deep-linkable as-of) now hold across the existing IA. This unblocks next iteration's J-44/J-45 QA, which will navigate via `?asof` deep links.

### Blueprint conformance
No new pages or nav changes. J-42 work lives on existing surfaces (cross-cutting presentation contract + `/data` under Data Manager); J-43 is the top-bar global control's serialization (cross-cutting, registered). Matches the blueprint's existing IA exactly.

### Data-contract additions
None — both values are already registered as approved [TARGET] rows in `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md`: "Resolved as-of date … **J-43 [TARGET]**" (serialize to `?asof` while historical, restored through the ONE global control, invalid → latest) and "**J-42 [TARGET]** — Displayed date format" (one shared frontend formatter, proposed `apps/frontend/lib/dates.ts:formatIsoDate`; `/data` fields become validated ISO text inputs). Build exactly to those rows; do not introduce a second formatter, a second date state, or any new endpoint.

## OUT OF SCOPE

- J-44 / J-45 (regime-history + index-series endpoints, dashboard card, detail-chart bands) — next iteration.
- J-46 (parallel fetch / vectorized backfill / benchmark script) and J-47 (≥100-term glossary + tooltips) — later iterations.
- J-22 / J-23 / J-24 — data-walled, honestly blocked-NA, non-halting per goal.md; do not attempt live fetches.
- Any backend API/DB/config date-shape change (contracts stay ISO and behaviorally unchanged).
- Rewriting page links to carry `?asof` manually — the provider/shell serialization is the single mechanism; do not scatter per-link date params beyond what the one mechanism produces.
- Restyling `/data` beyond the four input replacements; any unrelated refactor.

## DEFINITION OF DONE

- [ ] Target journeys J-42 and J-43 pass via browser-qa-agent, graded against the **verbatim** goal.md steps/acceptance (J-42: ISO display on /data form + job cards + coverage + diagnostics + switcher + indicator + chart tooltip, validated text inputs with blocked submit; J-43: select D → `?asof=D` in URL + click-through + reload + fresh tab restore + param disappears at latest + invalid param degrades to latest).
- [ ] Required-still-passing journeys remain green: J-13 (switcher re-points pages), J-18 (no page-local date state — judged per the J-43 amendment, NEVER on URL date-freeness), J-06 (detail scores equal leaderboard at the historical date — exercised within J-43 step 2), J-17 (the /data form still submits a job with the typed dates), J-20 (chart/tooltip behavior unchanged apart from formatting).
- [ ] No anti-goal violation introduced (esp. no second date state, no per-component format literal, no contract-shape change).
- [ ] Full backend pytest suite executed once with result counts recorded in the dev handoff; no regressions (expect ~621 pass / 4 skip / 0 fail; ~14 min).
- [ ] Frontend lint passes (`npm run lint` in `apps/frontend`; no frontend unit-test runner exists — validation behavior is verified via the browser error-state checks).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-42 and J-43 executed with steps/acceptance taken **verbatim from docs/goal.md** (do not paraphrase or invent journey text), plus re-verification of J-06, J-13, J-17 (form-submit leg only — no live provider fetch), J-18, J-20 on the touched surfaces. Capture **fresh, per-journey screenshots** named by journey ID (no recycled/byte-identical evidence — iter-0's was md5-flagged).
- Unit/integration: full backend pytest suite once (no code change expected to alter it — this closes the baseline gate gap). ISO input validation + `?asof` restore logic verified through the browser checks below since no frontend test runner exists.
- Error cases that MUST be exercised and rejected/handled:
  - `/data` date input `2026-13-40` → inline error, submit blocked.
  - `/data` date input `10/06/2026` → inline error, submit blocked.
  - `/stocks?asof=not-a-date` and `/stocks?asof=2026-01-01` (a date with no run, if absent from the run list) → latest view, switcher shows "Latest", no crash, no fabricated date.
  - Valid `?asof=<historical run date>` in a fresh tab → switcher shows that date + historical indicator; detail values match that date's stored snapshot.

## NOTES

- **QA environment gotchas (from session memory):** the Chrome MCP `select` action does not fire React `onChange` on this frontend — drive the as-of switcher via native-setter + bubbled change event in an evaluate call, then assert the live DOM. If every page renders as a dead un-hydrated shell (404 on `_next/static/chunks/main-app.js`), the dev server's `.next` was clobbered by a prod build — record SKIPPED, not FAIL, and flag it. Never broad-`pkill` dev servers on this machine — kill by port (backend 8835 / frontend 3835) only.
- **J-18 judging rule (memory + goal.md amendment):** `?asof=` in the page URL while historical is REQUIRED by J-43 — it is the serialization of the one state. Judge J-18 strictly on "no page-local independent date state", never on URL date-freeness.
- Next.js App Router note for the developer: reading `useSearchParams()` in the shell-mounted provider requires a `<Suspense>` boundary; use `router.replace` (no scroll, no history spam) for serialization writes; the provider stays the single reader/writer of `?asof`.
- Evaluator-recommended sequence after this iteration: iter-2 = J-44 + J-45 (shared stored-regime-history + server-side index-series endpoints per the blueprint [TARGET] rows), then J-47, then J-46.
- On verified completion, the next decomposer should flip the J-42/J-43 [TARGET] annotations in `blueprint.md` to built (additive bookkeeping, no re-approval needed).
