**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-5 (J-48 / J-50 / J-54)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration: 5
Snapshot SHA: ee2dabd8ff9dbe2d92ff045f2601fc289b997068

## Changed files

Frontend-only diff (no `apps/backend/` files changed — confirmed via `git diff`):

- `apps/frontend/components/asof-provider.tsx` — new `useAsOfHref()` export
- `apps/frontend/components/sidebar.tsx` — uses `useAsOfHref()` for nav hrefs
- `apps/frontend/app/stocks/page.tsx` — J-48 sort + J-50/J-54 href wiring
- `apps/frontend/app/stocks/[ticker]/page.tsx` — J-50 back-links + theme link
- `apps/frontend/app/scanner-runs/page.tsx` — J-50 run-row hrefs
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — J-50 back-link
- `apps/frontend/app/research/page.tsx` — J-50 `SubjectLeaderboardLink` href
- `apps/frontend/app/watchlist/page.tsx` — J-50 ticker row href
- `runs/.../state/blueprint.md` — status tags flipped from `iter-5+` to `iter-5 in flight`

---

## Step 1 — Data Contract check

**Registered values checked:** Leadership score / Entry Quality score / Risk score / bucket /
setup status / rank / Resolved as-of date.

### J-48 sort comparators (`apps/frontend/app/stocks/page.tsx`)

The `SORT_COMPARATORS` map (lines added in this diff) reads:

```
rank:          (a, b) => a.rank - b.rank
leadership:    (a, b) => a.leadership.score - b.leadership.score
entry_quality: (a, b) => a.entry_quality.score - b.entry_quality.score
risk:          (a, b) => a.risk.score - b.risk.score
setup:         (a, b) => a.setup.status.localeCompare(b.setup.status)
```

Each expression reads a field from the already-served API row — `rank`, `.score`, `.status`. No
arithmetic other than subtraction for ordering is applied; no score is re-derived from component
fields. The sort memo (`sorted = useMemo(...)`) re-orders the in-memory array; it does not alter
any displayed cell value. This is a pure view transform — blueprint invariant 13 ("View transforms
never recompute") is satisfied. No new endpoint, no second fetch.

**Finding:** no Data Contract violation.

### J-50 `useAsOfHref()` helper (`apps/frontend/components/asof-provider.tsx`)

The new export reads `{ asOf, isHistorical }` from `useAsOf()` — the ONE global context this file
already owns — and merges `asof=<D>` into the caller-supplied path when historical, or strips it at
latest. It does not hold a second date state, does not parse a date from outside the context, and
does not call any endpoint. This is a re-format of the existing "Resolved as-of date" contract row
into a link's query string, exactly as registered in the blueprint's Data Contract cross-cutting
entry for J-50.

**Finding:** no Data Contract violation.

### New displayed value check

The only new UI element is the sort-direction indicator (ArrowUp / ArrowDown / ArrowUpDown icon on
column headers). This is UI chrome with no data value — it is not a Data Contract entry. No new
numerical or label value is displayed that was not already served.

**Finding:** no unregistered value.

---

## Step 2 — Information Architecture check

**New pages/routes in this iteration:** none. The spec explicitly defers `/research/samples` to a
later iteration.

**Modified routes:**
- `/stocks` — sort + href changes (existing canonical home: Stocks)
- `/stocks/[ticker]` — href changes (existing canonical home: Stocks > Stock Detail)
- `/scanner-runs` + `/scanner-runs/[runId]` — href changes (existing canonical homes)
- `/research` — href change on one internal link (existing canonical home: Research)
- `/watchlist` — href change on ticker row links (existing canonical home: Watchlist)
- Sidebar — all 10 nav entries wrapped with `useAsOfHref()` (the nav itself is unchanged)

All modified surfaces are pre-existing, live under their registered canonical homes, and are
reachable via the persistent sidebar in ≤2 clicks. No parallel shell or duplicate home was
introduced. No new top-level section was added.

**Finding:** no IA violation.

---

## Step 3 — Advisory observations

None. The changes are consistent with the blueprint's intent. The `useAsOfHref()` helper is the
single canonical implementation for J-50 href embedding, as required by blueprint invariant 13.
The `SubjectLeaderboardLink` in `research/page.tsx` correctly uses `asofHref()` to merge the
`?asof` param into an already-present `?pattern=` / `?setup=` query string without clobbering it
(the helper's `URLSearchParams` merge logic handles this cleanly).

---

## Blueprint update

The blueprint's status tags for J-48/J-50/J-54 were flipped from `[TARGET — iter-5+]` to
`[TARGET — iter-5 in flight]`. This is a bookkeeping edit; no IA or Data Contract row was added
or removed, so no re-approval is triggered.
