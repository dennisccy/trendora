**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-13 (J-61 + J-62)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration index: 13
Snapshot SHA: 68c560f8dee0faeb5e98a05e2064a751ae508f85

---

## Step 1 — Data Contract check

### J-61: Per-date availability counts

Blueprint contract row: "ONE read-only derivation over stored bars + stored runs by the existing coverage machinery (`data_manager`)" served by "ONE new read-only endpoint in the availability family under `GET /api/data/...`".

**Canonical computation source check:**
`compute_availability` in `apps/backend/app/engine/data_manager.py` (lines 333+) calls the SAME `_trading_days(session, cfg)` function that `compute_coverage` uses (line 359 of the new function, referencing line 308 of `compute_coverage`). The `total_symbols` denominator is computed by the same `SELECT COUNT(DISTINCT symbol)` pattern `compute_coverage` uses for `symbol_count` (data_manager.py:304 vs new function:364). The `snapshot_set` is drawn from `ScannerRun.asof_date` — the same source `compute_coverage` uses for snapshot date detection (line 380 new fn vs line 300 existing).

No second derivation of any canonical score, return, bucket, or setup was introduced. The function reads stored rows only.

**Serving endpoint check:**
`GET /api/data/availability` added at `apps/backend/app/api/data.py:113` calls `data_manager.compute_availability(session, get_config())`. This is the one registered endpoint. No other endpoint or component fetches availability from a different route.

**Frontend consumption check:**
`apps/frontend/lib/api.ts` exports `fetchDataAvailability()` which calls `/api/data/availability` (the one canonical endpoint). `apps/frontend/app/data/page.tsx` imports and calls only `fetchDataAvailability`. `apps/frontend/components/availability-heatmap.tsx` receives the `AvailabilityResponse` as a prop (`state`) — it never fetches independently, never recomputes the backend values, and displays `cell.symbols_with_bars` and `cell.total_symbols` verbatim as served.

**Density bucketing check (potential "no magic numbers" / "duplicate computation" concern):**
The `densityBucket` function in `availability-heatmap.tsx` (lines 36–44) maps the served `symbols_with_bars / total_symbols` fraction to a 6-step presentation color bucket. This is **pure presentation** (frontend-only color ramp). The thresholds (0.25, 0.50, 0.75, 1.0) classify display color only and are not registered as a canonical value in the Data Contract. The backend never produces or stores a density-bucket value. This is a permitted "re-format is fine" pattern (skill §A3). Confirmed: no matching classification logic exists in `apps/backend/app/engine/` source.

**Heatmap click path check (no-second-date-state invariant 5):**
`handleHeatmapPrefill` in `apps/frontend/app/data/page.tsx` calls `setStart(s)` and `setEnd(e)` — the job form's date input state — never `setAsOf`. Confirmed at page.tsx lines 278–282. The `AvailabilityHeatmap` component's prop is `onPrefillRange`, which is wired to `handleHeatmapPrefill`. The component never imports `useAsOf` or touches the global as-of state.

No Data Contract violation for J-61.

### J-62: As-of calendar popover

Blueprint contract row: annotated on the existing "Resolved as-of date" row — "calendar popover is a PRESENTATION of the same one state, no new date source, no new endpoint, ISO yyyy-MM-dd via the shared formatter".

**`asof-provider.tsx` byte-unchanged:**
`git diff 68c560f8dee0faeb5e98a05e2064a751ae508f85 -- apps/frontend/components/asof-provider.tsx` produces no output. The provider and its `setAsOf` / `dates` / `asOf` / `isHistorical` / `latest` contract are byte-identical.

**No second date state in `AsOfCalendar`:**
`apps/frontend/components/asof-calendar.tsx` contains exactly one `useState` call: `const [view, setView] = useState(initial)` (line 74). `view` holds `{year, month0}` — the month navigation cursor, NOT an as-of value. It is never serialized, never passed to `onSelect`, and never written to any global state. `asOf` arrives as a prop (line 55) and is used only for display highlighting; the component never owns or modifies it. Selecting a day calls `onSelect(isLatest ? null : cell.iso)` and `onClose()` (lines 198–200). In `asof-switcher.tsx`, `onSelect` is wired to `setAsOf` from `useAsOf()` (line 91: `onSelect={setAsOf}`). One date owner confirmed.

**No second date state in `AsOfSwitcher`:**
`apps/frontend/components/asof-switcher.tsx` has one `useState`: `const [open, setOpen] = useState(false)` (line 27) — the popover open/closed visibility flag. No date state. `asOf` and `setAsOf` come entirely from `useAsOf()` (line 26).

**Calendar reads the same `dates` array:**
`AsOfCalendar` receives `dates={dates}` and `latest={latest}` props from `AsOfSwitcher` (lines 88–92 of the switcher diff). These are the same values from `useAsOf()` — the canonical `dates` array derived once from `GET /api/runs` by `asof-provider.tsx`. No new endpoint, no new date source.

**ISO date formatting:**
`AsOfCalendar` imports `formatIsoDate` from `@/lib/dates` (asof-calendar.tsx line 7) and uses it in `title={formatIsoDate(cell.iso)}` (line 197) and the "Latest" label (line 237). Compliant with J-42.

No Data Contract violation for J-62.

---

## Step 2 — Information Architecture check

### J-61 heatmap surface

The heatmap renders on `/data` (Data Manager). Per the blueprint IA:
```
└── Data Manager     /data    (J-61 availability heatmap [TARGET iter-13])
```
`/data` is reachable in 1 click from the sidebar (`apps/frontend/components/sidebar.tsx` line 40: `{ href: "/data", label: "Data Manager", icon: Database }`). No new page, no new nav section, no duplicate home for any entity.

### J-62 as-of switcher surface

The calendar popover replaces the presentation of the existing top-bar as-of switcher. Per the blueprint IA: "Cross-cutting (no page of their own): J-13/J-43 top-bar as-of switcher ... J-62 [TARGET iter-13] the switcher's PRESENTATION becomes a calendar popover". `AsOfSwitcher` is mounted in `apps/frontend/app/layout.tsx` (confirmed by sidebar/layout grep: `<AsOfSwitcher />`). No new page, no new nav section, no duplicate home.

No IA violation for J-61 or J-62.

---

## Step 3 — Advisory observations

None. All new values are registered in the blueprint (`J-61` availability row, `J-62` annotation on the as-of date row). Formatting is consistent (ISO yyyy-MM-dd via `formatIsoDate` throughout). The density→color mapping is an explicitly permitted frontend-only presentation transform.

---

## Summary

| Check | Result |
|---|---|
| J-61 availability — canonical source (`data_manager.compute_availability` over same stored tables as `compute_coverage`) | PASS |
| J-61 availability — served by ONE endpoint (`GET /api/data/availability`) | PASS |
| J-61 density bucketing — presentation-only, no backend classification | PASS |
| J-61 heatmap click — writes only job form `start`/`end`, never `setAsOf` | PASS |
| J-62 calendar — `asof-provider.tsx` byte-unchanged | PASS |
| J-62 calendar — only local state is month cursor (`view`), not an as-of value | PASS |
| J-62 switcher — `open` is the only new local state; `asOf`/`setAsOf` from provider | PASS |
| J-62 calendar — reads the same `dates` / `latest` from the provider, no new source | PASS |
| J-62 ISO date rendering — uses shared `formatIsoDate` from `lib/dates` | PASS |
| IA — J-61 heatmap on existing `/data` home, 1 click from sidebar | PASS |
| IA — J-62 popover on existing cross-cutting top-bar switcher, no new page | PASS |
| No new unregistered canonical values | PASS |

No objective violations found in Part A (Data Contract) or Part B (Information Architecture).
