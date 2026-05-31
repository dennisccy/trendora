# goal-i_can_see_the_wealthy_future-iter-8 Execution Plan

Delivers the **foundational keystone J-15 (snapshot-served reads) + J-13 (global as-of switcher)**
together, because they are the *same mechanism*: resolve as-of → load-or-create-once the immutable
snapshot → serve its STORED rows. Building them together re-points the critical read path **once**
instead of twice. Depth **full** (backend + frontend, changes the read path of 5+ endpoints, real
regression risk to 11 green journeys).

**Alignment check (no drift):** J-13/J-15 are explicit Must-have journeys + Key Capabilities #17/#18
in `docs/goal.md`, and the anti-goals *No recompute in the read path* and *On-demand snapshots stay
immutable & lookahead-free* are exactly what this iteration implements. The blueprint already carries
the iter-8 serving note + the "Resolved as-of date + available as-of dates" Data-Contract row. The
switcher is an **additive global top-bar control** — adds no sidebar section, moves no feature home →
**no `blueprint.reapproval-requested`**. J-12 / J-14 / J-16 are correctly OUT OF SCOPE. No drift.

**Core architecture insight:** the stored snapshot already contains *everything* these endpoints
display — `ScannerRun` (regime, breadth, new-high-low, candidate counts, benchmark, asof) + its
`ScannerResult` (full canonical stock row in `record_json`), `SectorScoreRow`, `ThemeScoreRow`
children. So re-pointing is **"resolve the run, reshape its stored children into the existing
payload, echo `asof_date`"** — the same thing `GET /api/runs/{run_id}` already does. NO new
computation is introduced; `run_scan` remains the single place each engine runs.

## What to Build

**Backend — re-point the read path to serve from the immutable snapshot (no recompute):**
- **As-of resolver** `resolve_run(session, as_of, cfg) -> ScannerRun` in `app/engine/scanner.py`:
  - `as_of` is `None` → the **latest stored** `scanner_runs.asof_date` (fallback to `latest_data_date`
    + create-once when no runs exist yet, so non-bootstrapped test DBs still work).
  - parse `as_of`; **unparseable → 422**; **future (> latest_data_date) → 400**; **no bar with
    date ≤ D → 400** (before history). Never fabricate.
  - else `get_run_for_date(D)` **or** `run_scan(session, D, cfg)` — create-once, INSERT-only into the
    append-only tables, bars ≤ D only. Immutability + no-lookahead are inherited from the existing
    `run_scan` (already unit-proven in iter-5); a **second** view reads the existing rows (no UPDATE,
    no duplicate).
- **Snapshot-serving helpers** (recommend a small `app/engine/snapshot_serving.py`, or thin functions
  reused by both `runs.py` and the re-pointed routers) that reshape a resolved `ScannerRun` + children
  into the **exact existing payload shapes** and echo the resolved `asof_date`.
- **Re-point these endpoints** to `resolve_run` + serve STORED rows — **never** call live
  `score_regime`/`score_stocks`/`score_sectors`/`score_themes`/`summarize_candidates`:
  - `GET /api/dashboard?as_of=` — regime panel, breadth, new-high-low, **candidate counts read from
    `candidate_counts_json`** (not recomputed), `asof_date` (already returned).
  - `GET /api/stocks?as_of=` (list) — stored `ScannerResult.record_json` rows; `{asof_date, benchmark, rows}`.
  - `GET /api/stocks/{ticker}?as_of=` (detail) — the SAME stored row (→ J-06 byte-identical); **add
    `asof_date`** (already present) / keep `benchmark`.
  - `GET /api/sectors?as_of=` — stored `SectorScoreRow` rows; **add `asof_date` echo**.
  - `GET /api/themes?as_of=` — stored `ThemeScoreRow` rows; **add `asof_date` echo**.
- `GET /api/stocks/{ticker}/bars?as_of=` — accept `as_of`, validate identically, return OHLCV bars +
  server MA series with **date ≤ D** (`bars_asof(D)` + `sma_series`). **Not** snapshot-stored (raw bars
  are not a recomputed score) — only the as-of slice + no-lookahead.
- **Watchlist coherence:** re-point `/api/watchlist` current Leadership/Entry/Risk + bucket + setup +
  invalidation to read the **latest resolved snapshot** stock row (the SAME row `/api/stocks` serves at
  latest) instead of live `score_stocks` — so J-06-on-write-surface + J-11 stay byte-identical, no
  second source.
- **Not changed:** `/api/runs`, `/api/runs/{run_id}`, `/api/system-health` (J-07/J-08/J-09/J-10).

**Frontend — global top-bar as-of switcher (re-format only, never recompute):**
- A global **as-of date switcher** in the app-shell header, present across the as-of-aware pages. Date
  options come from the canonical `GET /api/runs`; default selection = latest.
- Selecting a date re-points **Dashboard (`/`), Stocks (`/stocks`), Themes (`/themes`),
  Sectors (`/sectors`), Stock Detail (`/stocks/[ticker]`)** to that date by passing `as_of` to their
  fetches; switching back to latest restores the current view.
- A clear **"viewing as-of D (historical)"** indicator (top-bar badge/banner using the `--warn` token)
  whenever resolved date ≠ latest; normal state otherwise.

**Recommended state mechanism (resolve up front to avoid thrash):** a **client React context
provider** (`AsOfProvider`) in `layout.tsx` wrapping `{children}`, exposing
`{asOf, setAsOf, latest, isHistorical, dates}`. Rationale: it is naturally global, **survives
client-side navigation** (so `/` → `/stocks` keeps the selected date — required by J-13 step 3)
**without rewriting every sidebar/row `<Link>`**, and matches the existing all-client-component fetch
architecture (each page reads the hook value and adds it to its `useEffect` deps). *Alternative:* a URL
`?as_of=` search param (bookmarkable, better for deterministic evidence) — acceptable, **but** then the
as-of-aware sidebar links and the leaderboard→detail row links MUST propagate `as_of` (and the
non-as-of pages must ignore it); flag this extra surface if chosen. Either way the frontend only
changes *which date's stored values it fetches* — it computes no score/bucket/return.

## Agents Required

- **backend-data: yes** — `resolve_run` resolver + snapshot-serving helpers; re-point the 5 read
  endpoints + `/bars` + watchlist enrichment; the new/updated unit + integration tests (resolver,
  create-once/immutability, no-lookahead on on-demand creation, snapshot-served coherence, no-recompute
  assertion, error cases, watchlist coherence).
- **frontend-ux: yes** — `AsOfProvider` + `AsOfSwitcher` + historical indicator; wire the `as_of` param
  through `lib/api.ts` fetchers; read the hook in the 5 as-of-aware pages.
- developer: yes — a single developer agent owns both backend and frontend (TDD).

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

**Backend**
- `apps/backend/app/engine/scanner.py` — ADD `resolve_run(session, as_of, cfg) -> ScannerRun`
  (default-latest, parse/validate → 422/400, create-once via existing `run_scan`). No new scoring math,
  no date/scoring literal (reuse config + `latest_data_date`).
- `apps/backend/app/engine/snapshot_serving.py` *(new, recommended)* — reshape a resolved `ScannerRun`
  + children into the existing `dashboard` / `stocks` / `stock_detail` / `sectors` / `themes` payloads
  (rehydrate `record_json`; read `SectorScoreRow`/`ThemeScoreRow`). Optionally refactor `runs.py`
  `run_detail` to reuse the dashboard/stocks shaping (low-risk; keep J-08 output identical).
- `apps/backend/app/api/dashboard.py` — accept `as_of`; serve from `resolve_run` (regime/breadth/
  candidate-counts read from stored run; drop live `score_regime`/`score_stocks`/`summarize_candidates`).
- `apps/backend/app/api/stocks.py` — re-point `/stocks` + `/stocks/{ticker}` to the resolved snapshot's
  stored rows; re-point `/stocks/{ticker}/bars` to accept + validate `as_of` and slice `bars_asof(D)`.
- `apps/backend/app/api/sectors.py` — accept `as_of`; serve stored `SectorScoreRow`; echo `asof_date`.
- `apps/backend/app/api/themes.py` — accept `as_of`; serve stored `ThemeScoreRow`; echo `asof_date`.
- `apps/backend/app/api/watchlist.py` — enrich from the latest resolved snapshot row (same row
  `/api/stocks` at latest serves), not live `score_stocks`.
- `apps/backend/tests/test_api_engine.py` — re-pointed endpoint coherence (list↔detail byte-identical
  → J-06), `asof_date` echoed on all five, **no-recompute** assertion (monkeypatch the live engines to
  raise → endpoint still 200 from storage for an already-persisted date), error cases (future/no-bars/
  unparseable → 4xx).
- `apps/backend/tests/test_scanner.py` (or new `tests/test_asof_resolver.py`) — resolver: a given
  `as_of` → correct stored snapshot; default → latest stored run; create-once on a not-yet-stored seed
  date, **second view = no UPDATE / no duplicate** (assert run + child row counts + identity);
  no-lookahead on on-demand creation (extend the existing walk-forward guard).
- `apps/backend/tests/test_api_watchlist.py` — watchlist current values still byte-identical to
  `/api/stocks` at latest (now both from the stored row).
- `apps/backend/tests/test_bars.py` — `/bars?as_of=D` returns only bars ≤ D + MA series; bad `as_of` → 4xx.

**Frontend**
- `apps/frontend/lib/api.ts` — add optional `asof?: string` to `fetchDashboard`, `fetchStocks`,
  `fetchStock`, `fetchSectors`, `fetchThemes`, `fetchStockBars` (append `?as_of=` when set). (Sectors/
  Themes response types already carry `asof_date`.)
- `apps/frontend/components/asof-provider.tsx` *(new)* — client context; loads `fetchRuns()` dates;
  `{asOf, setAsOf, latest, isHistorical, dates}`; default = latest.
- `apps/frontend/components/asof-switcher.tsx` *(new)* — top-bar `Select` of run dates + reset-to-latest
  + "viewing as-of D (historical)" indicator (Badge `variant="warn"`).
- `apps/frontend/app/layout.tsx` — wrap `{children}` in `<AsOfProvider>`; mount `<AsOfSwitcher/>` in the
  existing `<header>` (next to `<HealthBadge/>`).
- `apps/frontend/app/page.tsx`, `app/stocks/page.tsx`, `app/themes/page.tsx`, `app/sectors/page.tsx`,
  `app/stocks/[ticker]/page.tsx` — read `asOf` from the hook; pass to the fetcher; add to `useEffect`
  deps so a date change re-fetches.

## UI Evolution

- **New user-facing capability:** time-travel the whole primary dashboard — pick any past trading day
  from a global switcher and see Dashboard, Stocks, Themes, Sectors, and Stock Detail exactly as the
  scanner recorded them on that date, clearly labelled historical. Pages now render from persisted
  immutable snapshots (served from storage, not recomputed per request).
- **New information displayed:** the resolved as-of date on each page; a "viewing as-of D (historical)"
  indicator; the switcher's list of available dates (from `GET /api/runs`). Score/regime/sector/theme/
  setup meanings are unchanged — now sourced from the stored snapshot for the resolved date.
- **New user actions:** the global top-bar as-of date switcher (select a past date; reset to latest).
- **UI surface changes:** a new global top-bar control + historical indicator across the as-of-aware
  pages. **No new page/route, no sidebar change.**
- **Navigation changes:** none (additive top-bar control only).

## Visual Requirements

- **Component patterns:** reuse `Select` (`components/ui/select`) for the date picker and `Badge`
  (`variant="warn"`) for the historical indicator — no raw `<div>` soup. Keep the dense, dark
  analytical-workstation style; dates monospace/tabular (`.num`).
- **Layout:** the switcher sits in the existing sticky top-bar `<header>` (h-14, `bg-surface`,
  `border-b`), aligned with `HealthBadge`. The historical banner reads as a clear amber strip/badge.
- **Key visual effects:** `--warn` (#fbbf24) amber for the historical state; the normal/latest state is
  visually quiet (no warn colour). No invented colours/effects.
- **States to handle:** dates loading (switcher disabled/skeleton); `/api/runs` unavailable (switcher
  degrades to latest-only, no crash); latest (normal) vs historical (warn indicator); each page keeps
  its existing loading/empty/"Backend unavailable" treatments while re-fetching on a date change.

## Key Test Scenarios

- **J-15 (browser):** load `/stocks` at latest, reload, then `/`, `/themes`, `/sectors` — rows render
  from the stored snapshot, warm load fast (< ~1.5 s), and a stock's three scores match its Stock
  Detail page (coherence preserved).
- **J-13 (browser):** on `/`, open the switcher, select a past trading day; `/`, `/stocks`, `/themes`,
  `/sectors` all reflect that date and match that date's Scanner Run (not latest); a clear "viewing
  as-of D (historical)" indicator is visible; switch back to latest restores the current view.
  (**Distinct, md5-checked per-journey evidence**: a historical view on ≥2 pages + the indicator + the
  back-to-latest restore.)
- **Regression smoke (browser):** J-01 (dashboard panels render), J-02 (leaderboard filters still
  work), J-06 (NVDA list == detail), J-07 (open the Risk-Off run → zero Actionable).
- **Backend unit/integration:** resolver default→latest + correct stored snapshot + `asof_date` echoed;
  **create-once / immutability** (second view = no UPDATE, no duplicate rows); **no-lookahead** on
  on-demand creation (bars ≤ D only); **snapshot-served coherence** — `/api/stocks` list ↔
  `/api/stocks/{ticker}` byte-identical (J-06), iter-5 faithful-equality (stored latest == live) still
  holds; **watchlist coherence** equals `/api/stocks` latest; **no-recompute** — re-pointed endpoints
  serve a persisted date without invoking the live engines; **error cases** future/no-bars-≤-D/
  unparseable `as_of` → explicit 4xx (never a fabricated snapshot/score). Full existing suite (179+) green.

## Definition-of-Done Handoffs (chronically missing — must be produced)

- Dev handoff → `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-dev.md`.
- Audit handoff → `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-8-audit.md` (full-depth pipeline;
  missing for 7 consecutive full-depth iters per the spec — the auditor must write it this iteration).

## Notes / Assumptions (documented, not blocking)

- **Resolver HTTP codes:** unparseable `as_of` → **422**; future or before-history → **400**. Any 4xx
  satisfies the spec's "explicit 4xx (no fabrication)"; chosen for FastAPI convention. Documented so the
  reviewer/QA assert a *specific* code.
- **Non-trading-day `as_of` within range:** the UI only ever sends canonical run dates from
  `/api/runs` (all real trading days, instant). For a hand-typed in-range date the resolver treats
  "≥1 bar with date ≤ D and D ≤ latest" as resolvable (create-once). If the developer prefers to reject
  a date with no bar *exactly on* D (snap-to-trading-day), that is acceptable provided the create-once
  test for a real seed trading day still passes — document whichever rule is implemented.
- **Harness gaps (runner-script scope, NOT product — do not "fix" via product code):** the dedicated
  browser-qa has SKIPed on an HTTP-000/CORS flap for 7 iters. If it SKIPs again, reconcile from on-disk
  evidence and, if needed, boot services directly with `CORS_ORIGINS=http://localhost:<frontend-port>`
  and the frontend rebuilt with `NEXT_PUBLIC_API_URL=http://localhost:8835`; await a value unique to the
  historical state (the as-of date string or the "(historical)" indicator), not placeholder-shared text.
- **Highest-risk regressions** (DoD requires re-proving, not assuming): J-06 (both views read the SAME
  stored row), J-11 (watchlist == `/api/stocks` latest), and the criticals (on-demand snapshot
  immutability + no-lookahead).
