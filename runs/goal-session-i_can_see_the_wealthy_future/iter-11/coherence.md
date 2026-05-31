**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-11 (VCP detection, J-16)

- **Session:** i_can_see_the_wealthy_future
- **Iteration:** 11 — VCP (Volatility Contraction Pattern): a config-driven pattern flag riding the immutable snapshot, filterable + explained + forward-tested
- **Snapshot SHA audited:** `461a3cf0625961d5baf67bae5616c637ea1121a8` (`git diff <sha>` + uncommitted working tree)
- **Auditor:** coherence-auditor

This iteration adds Trendora's first detected price pattern. The design deliberately rides existing
seams (the per-stock row, the existing `/api/stocks` + `/api/stocks/{ticker}` + `/api/system-health`
endpoints, the existing snapshot tables, the shared forward-test grouping helper). I checked it against
the blueprint's pre-registered iter-11 Data-Contract rows and IA homes. **No objective Part A or Part B
violation.** A handful of advisory notes only.

---

## Part A — Data Contract (the "numbers don't match" gate) — PASS

The blueprint registers two additive rows this iter (`blueprint.md:87` VCP flag; `blueprint.md:89`
extended forward-aggregates row with `by_vcp`). The landed code conforms to both.

### A1 — VCP flag: ONE computation, faithfully stored, served from canonical sources ✓
- **Single computation.** `detect_vcp(...)` is called exactly **once per stock per run** inside the
  canonical scoring pass and composed onto the row alongside `setup`/`invalidation`/`themes`:
  `apps/backend/app/engine/scoring.py:335` (`vcp = detect_vcp(inv_closes, highs(bars), lows(bars), volumes(bars), cfg.patterns.vcp)`)
  → attached at `scoring.py:348` (`"vcp": vcp`). The detector (`apps/backend/app/engine/patterns.py`)
  is a pure function that imports **only** `VcpCfg` (`patterns.py:32`) — it never reaches into
  `score_stocks`, `classify_setup`, `ALL_STATUSES`, or the DB, so there is no parallel compute path.
- **Faithful mirror, not a second source.** `run_scan` writes the full block losslessly to
  `record_json` AND a denormalized typed mirror `is_vcp` **in the same transaction, from the same
  `row` dict**: `apps/backend/app/engine/scanner.py:105-108` (`record_json=json.dumps(row)` and
  `is_vcp=row["vcp"]["flagged"]`). This is byte-identical in role to the already-blessed
  `setup_status=row["setup"]["status"]` / `leadership_bucket` mirrors — one `detect_vcp` output, stored
  twice in one write, never recomputed. `apps/backend/app/models.py:165` adds the single APPEND-only
  column (`is_vcp: bool = Field(default=False, index=True)`). This matches `blueprint.md:87` verbatim.
- **Canonical source, no new endpoint.** `git diff --stat apps/backend/app/api/ apps/backend/app/main.py`
  is **empty** — VCP rides the existing `/api/stocks` (list) + `/api/stocks/{ticker}` (detail), which
  already rehydrate the `StockRow` from the stored `record_json` (`models.py` docstring). Leaderboard
  and detail therefore serve the **byte-identical stored row** → J-06 holds structurally.

### A2 — `by_vcp` reuses the single aggregation, reads the stored flag verbatim ✓
- `compute_forward_aggregates` adds `"is_vcp": res.is_vcp` to each observation **read verbatim from the
  stored column** (`apps/backend/app/engine/forward_testing.py:427`, comment "stored VCP flag (verbatim
  — never re-detected here)").
- The cohort breakdown reuses the **same** `_group_means` helper as every other dimension:
  `forward_testing.py:464` (`_group_means(stock_obs, "is_vcp", "vcp", [True, False], pad=True)`) — the
  identical signature used by `by_bucket` (`:476`), `by_setup` (`:477`), `by_regime` (`:478`). No second
  formula, no new module, no new endpoint. Served by the existing `GET /api/system-health` (no api/
  diff). Matches `blueprint.md:89`.

### A3 — Frontend is pure re-display (no client recomputation / non-canonical source) ✓
- Type-layer only in `apps/frontend/lib/api.ts` (`Vcp` interface + `vcp` on `StockRow`; `ForwardVcpRow`
  + `by_vcp` on `SystemHealthResponse`) — **no new fetcher** (`grep vcp lib/api.ts | grep fetch//api`
  empty; VCP rides the existing fetchers).
- The `/stocks` VCP filter narrows on the **server-computed** `r.vcp.flagged` — pure client-side
  re-display, no recompute, no re-sort (`apps/frontend/app/stocks/page.tsx`, `visible` memo +
  comment "never re-sorts or recomputes a score/flag").
- Badges/cards render the server-built `reason` / `invalidation.note` **verbatim** and only **format**
  `pivot` (`.toFixed(2)`) — `stocks/page.tsx` `vcpTitle`, `stocks/[ticker]/page.tsx` `VcpBadge`/`VcpCard`.
- `grep "flagged *=" apps/frontend` → **zero matches**: the frontend never assigns/derives a flag.
  Re-format of a canonically-served value is explicitly allowed (methodology A3).

### A4/A5 — New-value registration ✓
- VCP is **genuinely new** and explicitly **separate** from the registered setup status:
  `apps/backend/app/engine/setups.py` is **UNCHANGED** (empty diff) — VCP never enters `ALL_STATUSES`,
  never feeds `classify_setup`. So it is **not** a synonym/re-derivation of an existing registered value
  (no A4 duplicate). Both new values (the VCP flag + `by_vcp`) are **registered** in the Data Contract
  this iter — no A5 unregistered-value WARN.

---

## Part B — Information Architecture (the "where do I find it" gate) — PASS

- **No new route/page/feature.** Only the three existing route files changed
  (`git diff --stat 'apps/frontend/app/**/page.tsx'` → `stocks/[ticker]/page.tsx`, `stocks/page.tsx`,
  `system-health/page.tsx`). All three are **existing IA homes** in the blueprint nav skeleton:
  `/stocks` (`blueprint.md:37`), `/stocks/[ticker]` (`blueprint.md:38`), `/system-health`
  (`blueprint.md:42`).
- **No nav-skeleton change.** `git diff --stat apps/frontend/components apps/frontend/app/layout.tsx`
  is **empty** — the sidebar/shell is untouched. Correctly **no `blueprint.reapproval-requested`** this
  iter, exactly as the spec's "Blueprint conformance" and `blueprint.md:111` (iter-11 serving note)
  state.
- **No duplicate home / parallel shell.** The VCP filter + badge live inside the existing `/stocks`
  table; the detail badge/card inside the existing detail page; the `by_vcp` panel alongside the
  existing breakdown panels via the shared `BreakdownPanel`. Nothing creates a second home for an
  existing entity or its own layout.

---

## Part C — Advisory (non-blocking)

1. **Formatting consistency — clean.** `pivot` is rendered `$X.XX` (`.toFixed(2)`) on both the
   leaderboard tooltip and the detail badge/card; `invalidation.note` is rendered verbatim on every
   surface; the cohort labels match backend↔frontend (`VCP_LABELS = {True: "VCP", False: "non-VCP"}`
   in `forward_testing.py:62` ↔ the rendered `r.vcp` label in `system-health/page.tsx`). No drift.
2. **Config values diverged slightly from the spec's illustrative set** (the developer added
   `patterns.vcp.min_contraction_pct` and used `max_contractions: 3`, `contraction_shrink_ratio: 0.9`,
   `max_last_contraction_pct: 12`). The iter spec **explicitly delegated** final values to the developer
   ("the developer finalizes exact values… values are tunable hypotheses"), and every threshold lives in
   `config.yaml :: patterns.vcp` (no magic numbers). Not a coherence concern — noted only for traceability.
3. **`vcp.contractions` / `vcp.detail`** are new explainability sub-fields that ride the same registered
   `vcp` block; the contract row names them (`{… contractions, detail}` at `blueprint.md:87`), so they
   are registered, not orphaned.

---

## Pre-registered checks (from the iter-11 spec / coherence pre-note) — all satisfied

| Check | Result | Evidence |
|---|---|---|
| `is_vcp` is a faithful mirror (one `detect_vcp`, not a second source) | PASS | `scanner.py:105-108` — `record_json` + `is_vcp` from the same `row` dict in one transaction |
| `by_vcp` reads the stored flag verbatim via the shared helper | PASS | `forward_testing.py:427` (`res.is_vcp`) + `:464` (same `_group_means` as by_setup/by_bucket) |
| No new endpoint / no server-side VCP query param | PASS | `git diff --stat apps/backend/app/api apps/backend/app/main.py` empty |
| VCP separate from setup status (not a duplicate concept) | PASS | `setups.py` unchanged; VCP composed alongside `setup` in `scoring.py:335-348` |
| No client-side flag computation (single source on the read path) | PASS | `grep "flagged =" apps/frontend` empty; filter reads `r.vcp.flagged` |
| All surfaces are existing IA homes; no nav change → no reapproval | PASS | only 3 existing page.tsx changed; no sidebar/layout diff |

---

## Decision

Every new displayed value traces to **one** computation (`detect_vcp`), is **stored once** (lossless
`record_json` + a faithful same-transaction mirror), and is **served from its canonical endpoints**
(`/api/stocks`, `/api/stocks/{ticker}`, `/api/system-health`) — the forward-test `by_vcp` cohort reuses
the single existing aggregation path and reads the stored flag verbatim. The frontend re-formats only.
All three UI surfaces land in their existing IA homes with no nav-skeleton change. No duplicate
computation, no non-canonical source, no hidden/duplicate-home feature.

**Verdict: COHERENCE-PASS** — no objective violations; advisory notes only. No consolidation work is
handed to the next iteration.
