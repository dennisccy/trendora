**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-11 (J-58: Sectors page config-named/described ETFs with universe members)

Session: i_can_see_the_wealthy_future_forever_with_my_loved_ones
Iteration: 11
Snapshot SHA: 23832d73792632932bdc337a3953c60d1b5682ad

---

### Step 1 — Data Contract check

**Registered value under audit:** Sector/industry score (+RS-vs-SPY, dist-52w, trend)
- Canonical compute: `sectors:score_sectors`
- Canonical endpoint: `GET /api/sectors`

**New values introduced:** `description` (config one-liner) and `members` (universe-member list) — both
registered in the blueprint as additive reference metadata on the existing Sector-score Data Contract row.

**Duplicate computation check:**
- No new function computes any registered score/return/bucket/rank value independently. The
  `score_sectors` function at `apps/backend/app/engine/sectors.py:71` remains the single canonical
  compute path. The score/rank/RS-vs-SPY/dist-52w/trend math is unchanged.
- The `description` and `members` fields are config-derived reference data resolved once in
  `score_sectors` and stored into the immutable `SectorScoreRow` snapshot. They are echoed verbatim
  by `snapshot_serving._sector_row` at `apps/backend/app/engine/snapshot_serving.py:114-115` — no
  recomputation in the read path (invariant 2 satisfied).

**Non-canonical source check:**
- `apps/frontend/app/sectors/page.tsx` fetches from `GET /api/sectors` (the canonical endpoint). The
  `description` and `members` fields are rendered from the served payload — no client-side recomputation.
- `useAsOfHref` is imported from the canonical `@/components/asof-provider` (page.tsx:7), the same
  helper used by `/themes` (J-57). No second date-carrying path introduced.
- `apps/frontend/lib/api.ts` extends `SectorRow` with `description: string | null` and `members: string[]`
  (api.ts:109-110) — type-only, no fetch path change.

**Unregistered new values:**
- None. `description` and `members` are explicitly registered in the blueprint's J-58 note on the
  Sector-score Data Contract row. No genuinely new unregistered value introduced.

**Verdict for Step 1: no violations.**

---

### Step 2 — Information Architecture check

**New pages/routes introduced:** zero. All changes are on the existing `/sectors` route.

**Existing canonical home:** `/sectors` is the registered J-04 home in the IA skeleton, already
reachable as a top-level sidebar link (`apps/frontend/components/sidebar.tsx:34`: `{ href: "/sectors",
label: "Sectors", icon: Grid2x2 }`). Zero nav changes in this iteration (sidebar diff is empty).

**Reachability:** 1 click from any page via the persistent sidebar. No change.

**Duplicate home:** none introduced. All new UI (description, member chips, +n toggle, empty state) lives
inside the existing `/sectors` expanded panel — a secondary view within the already-canonical home, not
a new page.

**Parallel shell:** none. The expanded panel uses the existing page layout shell; no new layout wrapper
was introduced.

**Verdict for Step 2: no violations.**

---

### Step 3 — Subjective observations (advisory)

None. The member-chip styling and `+n` control mirror the J-57 themes pattern exactly
(`MEMBER_PREVIEW_LIMIT = 6`, `useAsOfHref`, `stopPropagation` in the non-clickable expanded `<tr>`),
keeping the two pages visually consistent.

---

### Summary

| Rule | Result |
|------|--------|
| No duplicate computation of registered values | PASS |
| No non-canonical source for registered values | PASS |
| No unregistered values that duplicate existing concepts | PASS |
| All new UI surfaces have a navigation path (≤2 clicks) | PASS (no new surface) |
| No duplicate home for an existing entity | PASS |
| No parallel shell | PASS |
| Coherence invariants 1–13 | PASS |

No violations found in either the Data Contract or the Information Architecture audit.
