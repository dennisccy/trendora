**Verdict:** COHERENCE-PASS

## Coherence Audit — goal-mcp-loop iter-1

**Session:** mcp-loop | **Iteration:** 1 | **Iter name:** goal-mcp-loop-iter-1
**Snapshot SHA:** 4cfc1e5c1caf3df30cda83c2d053ab91ebf97134
**Audited:** 2026-06-29

---

## Step 1 — Data Contract (objective)

### Registered values checked

**Evidence status + certified-claim** (`GET /api/evidence` → `proven_signals` map):

- Canonical computing module: `app.engine.evidence:build_evidence_payload` — implemented at
  `apps/backend/app/engine/evidence.py:79`. Reads ledger rows via `app.engine.ledger:read_entries`
  only; never recomputes any score or regime value; projects `verdict.status == STATUS_PASS` (read
  from the referee's written verdict) into the `proven` boolean on each claim row. No duplicate
  computation exists anywhere in the diff or the untracked new files.
- Canonical endpoint: `GET /api/evidence` — implemented at `apps/backend/app/api/evidence.py:21`,
  registered in `apps/backend/main.py:130`. Single serving endpoint; no second endpoint for this
  value was introduced.
- Frontend consumption: both `/stocks/page.tsx` and `/stocks/[ticker]/page.tsx` call
  `fetchEvidence()` → `GET /api/evidence` to obtain the `proven_signals` map; no alternative fetch
  path. The `resolveEvidenceStatus` helper (`apps/frontend/lib/evidence.ts:81`) is a pure lookup on
  the served map — it reads the backend-computed `claim.proven` boolean and returns a display label;
  it does NOT independently derive proven-ness from `verdict.status`. This is re-formatting, not
  recomputation.
- `/evidence` page (`apps/frontend/app/evidence/page.tsx`) fetches exclusively from
  `fetchEvidence()` → `GET /api/evidence`; renders data verbatim.

**Three per-stock scores (Leadership / Entry Quality / Risk):**

The diff and untracked files add `EvidenceStatusBadge` alongside existing `ScoreBadge` /
`ScoreCard` elements. The score values and their computation path (`scoring:score_stocks` →
`GET /api/stocks`, `GET /api/stocks/{ticker}`) are untouched. No recompute in the read path.

**Market regime, sector, theme, forward-return values:** unchanged; no new computation paths.

**New unregistered value check:** No new displayed value was introduced that is conceptually
the same as an existing registered value. The only new display is the "Proven / Not yet proven"
badge, which is the already-registered Evidence status value (Data Contract row 1). No WARN for
unregistered values.

**Result: no Data Contract violations.**

---

## Step 2 — Information Architecture (objective)

### New page/route: `/evidence`

- **Blueprint canonical home:** the blueprint IA skeleton explicitly lists `Evidence [NEW] /evidence`
  as an approved top-level nav section (slot: after Research). The iteration implements this
  already-approved entry — no new home was invented.
- **Navigation path:** `apps/frontend/components/sidebar.tsx` line 41 contains
  `{ href: "/evidence", label: "Evidence", icon: ShieldCheck }` in the persistent `NAV` array,
  placed after the Research entry. This is a top-level sidebar link — reachable in **1 click** from
  any page. Verified via static read of the nav array.
- **No parallel shell:** `apps/frontend/app/evidence/page.tsx` uses the standard `PageHeading` +
  `Card` layout components inside the existing app shell. No new layout wrapper or second sidebar
  introduced.
- **No duplicate home:** Evidence is a genuinely new entity (the certified-claims ledger); it has no
  prior home in the IA.

### Inline badges on existing surfaces

`EvidenceStatusBadge` is an inline chip added to `/stocks` leaderboard rows and `/stocks/{ticker}`
score cards. These are additive elements on existing surfaces — not new pages/routes. The existing
IA homes for Stocks and Stock Detail are unchanged; no IA check triggered.

**Result: no IA violations.**

---

## Step 3 — Advisory observations (WARN only)

**WARN (minor DRY):** The `SCORE_SIGNALS` constant mapping the three score names to their
evidence-ledger signal keys is defined identically in two files:
`apps/frontend/app/stocks/page.tsx` (around line 23) and
`apps/frontend/app/stocks/[ticker]/page.tsx` (around line 34):

```typescript
const SCORE_SIGNALS = {
  leadership: "leadership_score",
  entry_quality: "entry_quality_score",
  risk: "risk_score",
} as const;
```

Both still read from the same `GET /api/evidence` endpoint — no data contract violation. This is a
minor DRY issue: a future iteration could extract `SCORE_SIGNALS` to `apps/frontend/lib/evidence.ts`
(alongside the existing `PROVEN_LABEL` / `NOT_PROVEN_LABEL` constants) so there is one canonical
definition. Advisory only; does not block the goal.

---

## Summary

| Check | Result | Note |
|---|---|---|
| Part A — Data Contract | PASS | Single canonical module (`build_evidence_payload`) + single endpoint (`GET /api/evidence`); no duplicate computation; frontend reads served map, never recomputes |
| Part B — IA | PASS | `/evidence` page in blueprint-approved home; top-level sidebar link (1 click); no parallel shell; no duplicate home |
| Part C — Advisory | WARN | `SCORE_SIGNALS` duplicated across two files; no coherence impact |

**Verdict: COHERENCE-PASS** — no objective violations in Part A or Part B.
