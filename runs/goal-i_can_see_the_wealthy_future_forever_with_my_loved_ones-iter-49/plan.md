# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-49 Execution Plan

Two small, independent, user-facing wins (J-106 + J-108). J-107 (Factor Lab restructure) is
explicitly OUT OF SCOPE — deferred to iter-50. Do NOT touch the research read path, EventStudyCache,
or `compute_factor_lab`. This is NOT a GOAL_ACHIEVED candidate, so the full-suite gate is
non-load-bearing here — run it nohup-async and never block the evaluator.

## What to Build
- **J-106** — Add a sortable **"Proximity to 52w high"** column to the `/stocks` leaderboard, placed
  directly after the **Risk** column. It re-displays the already-served `high_proximity` Leadership
  `ScoreComponent` value (`dist_high`, ≤ 0; 0 at a fresh high; NA on short history). No new served
  field, no recompute, no `/api/stocks` payload change.
- **J-108** — Diagnose, document, and fix the root cause of the readiness/health request path so the
  top-bar badge honestly reaches **Ready** / **Initializing… n/m** when the backend is genuinely
  serving, instead of being stuck on "Backend unavailable" — including when the frontend is opened at
  the `dev.sh`-printed LAN-IP origin.

## Agents Required
- backend-data: yes — minimal only: confirm/refute the CORS/host hypothesis and widen the dev CORS
  allowance if confirmed (`scripts/dev.sh` and/or `apps/backend/main.py`); confirm `readiness.py`
  readiness states are unchanged. Possible small `/api/methodology` glossary-catalog addition if the
  proximity term is missing (see Risks) — must NOT alter `/api/stocks`.
- frontend-ux: yes — the new leaderboard column + sort + tooltip, and the host-aware `API_BASE` fix.
- developer: yes — single developer agent implements both backend and frontend with TDD.

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/app/stocks/page.tsx` — new "Proximity to 52w high" `SortHeader` after the Risk header
  + matching `<td>` after the Risk `ScoreBadge` cell; new `SortKey`; a `highProximityAt(row)` helper
  reading the `high_proximity` component from `row.leadership.components`; an **explicit NA-last
  comparator branch** in `comparatorFor` (do NOT route it through `SORT_COMPARATORS` — that path has no
  null handling); a colour/NA-honest cell; `term=` tooltip on the header; `aria-label="Sort by
  Proximity to 52w high"`.
- `apps/frontend/lib/api-base.ts` (NEW) — extract a pure, exported `resolveApiBase(configuredBase,
  hostname, port)` so it is unit-testable under the existing `node lib/*.test.ts` pattern.
- `apps/frontend/lib/api.ts` — make `API_BASE` host-aware at runtime via `resolveApiBase(...)` used
  inside `getJSON`/`sendJSON` (guard `window` for SSR); keep an explicit non-localhost
  `NEXT_PUBLIC_API_URL` verbatim; otherwise, when the configured base is localhost but the page host is
  not, resolve the backend on `window.location.hostname` + `NEXT_PUBLIC_API_PORT`.
- `apps/frontend/lib/api-base.test.ts` (NEW) — assert the two resolution cases (localhost-config +
  non-localhost page host → page-host + configured port; explicit non-localhost `NEXT_PUBLIC_API_URL`
  → verbatim).
- `scripts/dev.sh` and/or `apps/backend/main.py` — IF the CORS/host hypothesis is confirmed: widen the
  dev CORS allowance so the LAN-IP frontend origin is accepted (compute `LOCAL_IP` before exporting
  `CORS_ORIGINS`, or add a dev-mode private-LAN origin allowance in `main.py`). Minimal, dev-only.
- `apps/backend/tests/test_*` — IF CORS is changed: a test that a request bearing the LAN-IP frontend
  origin is allowed, and that `readiness.py` states are unchanged.
- `docs/handoffs/goal-...-iter-49-dev.md` — handoff INCLUDING the diagnosed J-108 root cause (step 4).

## UI Evolution
- New user-facing capability: see each stock's distance below its 52-week high at a glance on the
  leaderboard and sort by it; the readiness badge now reads correctly on every page (a trust fix).
- New information displayed: per-stock proximity-to-52w-high (re-display of the stored Leadership
  `high_proximity` value).
- New user actions: click the new column header to sort the leaderboard by proximity-to-52w-high.
- UI surface changes: `/stocks` table gains one column after Risk; the readiness badge behavior is
  corrected (no new surface).
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing leaderboard `<table>` + `SortHeader` exactly; the new cell
  matches the existing numeric cells (`num`, right-aligned), with a muted "NA" like `ForwardReturnCell`.
- Layout: unchanged — one inserted column between Risk and Setup; no layout reflow beyond the new column.
- Key visual effects: none new — match the established leaderboard styling and the existing
  sort-indicator / hover / focus-ring affordances.
- States to handle: NA-honest cell (muted "NA", sorts last); loading skeleton and "Backend
  unavailable" error states are unchanged; the readiness badge keeps its three honest states
  (Ready / Initializing… n/m / Unavailable) — never faked.

## Test Strategy
- **Unit (frontend, `node lib/api-base.test.ts`):** localhost-config + non-localhost page host resolves
  to page-host + `NEXT_PUBLIC_API_PORT`; explicit non-localhost `NEXT_PUBLIC_API_URL` used verbatim;
  localhost page host stays localhost. Assert exact strings.
- **Unit (frontend):** if practical, a render/sort assertion for the proximity comparator (NA-last);
  otherwise rely on browser-qa per spec (J-106 is frontend-only).
- **Backend:** if CORS is changed, a pytest asserting the LAN-IP frontend origin is allowed and
  `readiness.py` states are unchanged. Backend suite via `cd apps/backend && .venv/bin/python -m
  pytest` — run the FULL suite nohup-async (never concurrent with browser probes; never block the
  evaluator).
- **Browser-qa (Frontend Present: yes — required), plan the Playwright fallback UP FRONT** (Chrome MCP
  CDP has repeatedly emptied the evidence dir on this host; `md5sum` the evidence dir first; reject
  blank/skeleton/byte-identical frames):
  - **J-106:** the new column renders directly after Risk; a row's value EQUALS what that ticker's
    Leadership breakdown shows for `high_proximity`; sorting by the column reorders the table (capture
    two byte-distinct frames); a null value renders NA and sorts last; the header tooltip surfaces the
    glossary copy.
  - **J-108:** with a freshly-restarted, warmed, single-fetch-at-a-time backend the badge reaches Ready
    (or Initializing… n/m); **exercise the diagnosed failing scenario — open the frontend at the
    dev.sh-printed LAN-IP origin** — and confirm the badge now reaches Ready (a localhost curl/open
    does NOT prove the fix; iter-45 lesson); with the backend genuinely down the badge shows
    Unavailable (honest, not faked).
  - **Required-still-passing smoke:** J-01 (dashboard hydrates), J-06 (detail == leaderboard), J-07
    (Risk-Off → 0 Actionable, CRITICAL), J-18 (0 native `input[type=date]`, CRITICAL), J-40, J-48 (a
    column sort reorders), J-75/J-80 (forward-return columns + header regime/theme strip), J-104 (a
    research lab still loads after the `API_BASE` change). Confirm data still loads on EVERY page after
    the `API_BASE` change.

## Risks / Watch-outs
- **Single source (critical):** the column MUST show the IDENTICAL value the detail-page Leadership
  breakdown shows for `high_proximity` (read the served `ScoreComponent`; format identically; never
  recompute). Browser-verify equality. Do NOT add `high_proximity` (or any field) to the `/api/stocks`
  payload — that trips the byte-equality / `set(payload)==` guards (iter-23/24/32 trap).
- **Glossary tooltip may be missing.** There is currently no config-backed glossary term for
  proximity-to-52w-high (not in the frontend `term=` set nor the backend methodology catalog).
  `TermInfo` silently renders no marker for an unknown term, which would FAIL the DoD ("header carries
  the config-backed glossary tooltip"). Dev must: (a) confirm the EXACT glossary term string and pass
  it to `term=`; or (b) if none exists, add the term to the SINGLE config-backed glossary catalog
  (backend `/api/methodology` source) — do NOT hardcode tooltip copy in the frontend (anti-goal:
  config-driven vocabulary). This is the one case where J-106 may need a tiny backend (methodology)
  change; it must NOT alter `/api/stocks` (mild deviation from the spec's "J-106 frontend-only" note —
  documented here, required to satisfy the DoD + anti-goal).
- **Comparator NA-safety:** a new sort key routed through `SORT_COMPARATORS[key]` would be `undefined`
  and crash, and a naive `a-b` would mis-place NA. Add an explicit NA-last branch (mirror `fwd_`/`mdd_`).
- **J-108 diagnose-before-fix:** document the root cause (J-108 step 4) BEFORE fixing. First disambiguate
  a genuine code bug from a contended/hung backend (iter-45): run on a freshly-restarted, warmed,
  single-fetch backend and verify the EXACT request path (URL + Origin + status) the browser uses. A
  localhost curl bypasses the CORS/host bug and cannot prove the fix.
- **Honest readiness (critical):** the badge must NEVER be hardcoded, inverted, stuck, or faked Ready
  when the backend is down. Verify the genuine-down case still shows Unavailable.
- **`API_BASE` is module-load-time today.** Making it host-aware must guard `window` (SSR) and must not
  break ANY existing fetcher — every page reads through `getJSON`/`sendJSON`. Smoke every page.
- **SSR safety:** `window.location` is only available client-side; the leaderboard and providers are
  client components, but ensure no resolution path executes during SSR.
- **Out of scope (exclude):** J-107 and any research-read-path / cache change; any canonical-score,
  Risk-Off→Actionable, as-of/`?asof`, or second-date-state change; J-22/J-23/J-24 (data-walled,
  non-vetoing).

## Key Test Scenarios (must pass for the iteration to be complete)
- The "Proximity to 52w high" column renders directly after Risk, equals the Leadership breakdown value
  for the same ticker, sorts NA-last (two byte-distinct frames captured), is NA-honest, and its header
  tooltip surfaces config-backed glossary copy.
- With a genuinely-serving backend opened at the LAN-IP origin, the readiness badge reaches Ready (or
  Initializing… n/m); with the backend down it shows Unavailable; the diagnosed root cause is documented
  in the dev handoff.
- All required-still-passing journeys remain green; data loads on every page after the `API_BASE`
  change; no anti-goal violation introduced.
