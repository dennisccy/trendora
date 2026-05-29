**Verdict:** COHERENCE-WARN

# Coherence Audit — goal-i_can_see_the_wealthy_future-iter-2

- **Session:** i_can_see_the_wealthy_future · **Iteration:** 2 (Indicators + Market Regime + Sector Leaderboard — first canonical values)
- **Audited against snapshot:** `ec53e1b86fa502450c982eb609da3338823e081f` (`git diff` + uncommitted/untracked)
- **Blueprint:** `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`
- **UI surface map:** present (`reports/phase-goal-i_can_see_the_wealthy_future-iter-2-ui-surface-map.md`)

## One-line summary

No objective Data-Contract or Information-Architecture violations. The first canonical values
(Market Regime, Sector Score, A–E bucket) are each computed in exactly one engine module and served
from exactly one canonical endpoint; the frontend recomputes nothing and the Dashboard's Top Sectors
correctly read `/api/sectors`. **WARN** (does not block) for two contract-bookkeeping notes the
decomposer should reconcile next — chiefly a breadth attribution that risks an iter-5 duplicate.

---

## Part A — Data Contract check (the "numbers don't match" gate)

**Result: no FAIL.** Single source of truth holds for every value displayed this iteration.

| Registered value | Canonical compute (blueprint) | Found compute site | Canonical serve | Found serve | OK? |
|---|---|---|---|---|---|
| Market Regime score + label | `app.engine.regime:score_regime` | `apps/backend/app/engine/regime.py:103` (only site) | `/api/dashboard` (iter-2 note) | `apps/backend/app/api/dashboard.py:28` | ✅ |
| Sector / industry score | `app.engine.sectors:score_sector` | `apps/backend/app/engine/sectors.py:64` (only site) | `GET /api/sectors` | `apps/backend/app/api/sectors.py:27` | ✅ |
| A–E bucket | `app.engine.buckets:to_bucket` | `apps/backend/app/engine/buckets.py:15` (only site) | rides on each score | `sectors.py:124` calls `to_bucket` | ✅ |
| RS-vs-SPY / dist-from-52w-high / trend label / components | (emitted by `score_sectors`) | `sectors.py:117-128` | `GET /api/sectors` | served verbatim | ✅ |

Evidence the single-source rule held:

- **Regime computed once, served once.** `score_regime` is the only definition; `dashboard.py:28`
  is the only caller and the only serving path. No `/api/runs/...` or second endpoint serves regime
  this iteration (the blueprint's iter-2 serving note authorises the on-request `/api/dashboard`
  model). No duplicate `score_regime`/`_compute_regime` exists in the diff.
- **Sector score computed once, served once.** `score_sectors` is the only definition; `sectors.py:27`
  serves it **verbatim** (`return score_sectors(...)`, no reshape/recompute). No second sector-score
  function in the diff.
- **A–E derived in one place only.** `to_bucket` (`buckets.py:15`) is the sole bucketing fn; called
  only from `sectors.py:124`. The frontend `ScoreBadge` (`components/score-badge.tsx:24`) receives the
  **server-provided** `bucket` letter as a prop and only maps it to a colour variant — it does **not**
  re-derive the bucket from the score. Frontend sweep for client-side bucket/score math returned only
  `<ScoreBadge bucket={row.bucket} score={row.score} />` in both pages (props, not computation).
- **Dashboard ↔ Sectors single source (the iteration's central risk).** The Dashboard does **not**
  re-serve the sector score: `dashboard.py` returns no sectors, and `app/page.tsx:42-47` calls
  `fetchSectors()` → `/api/sectors` and slices `rows.slice(0, 5)` (`page.tsx:96`). Same response object
  the Sector Leaderboard renders → numbers cannot diverge. ✅ (DoD "Top Sectors read `/api/sectors`")
- **Frontend recomputes nothing.** `lib/api.ts` is fetch + typed re-format only; `ComponentBreakdown`
  and `ScoreBadge` render server fields. No `.sort()`, threshold comparison, or score arithmetic in
  the frontend diff.
- **Blueprint edit was additive-only.** The only change to `blueprint.md` is six appended lines
  ("Iteration serving notes") — no IA row or Data-Contract row was modified or deleted. Matches the
  spec's promised additive note.

---

## Part B — Information Architecture check (the "where do I find it" gate)

**Result: no FAIL.** No new routes; both surfaces are existing IA homes reachable in 1 click.

- `/sectors` and `/` are pre-existing blueprint IA homes (nav skeleton lines 30–31). This iteration
  populates their empty states; it adds **no** new route.
- **Navigation path confirmed statically.** `apps/frontend/components/sidebar.tsx:27` (`{ href: "/",
  label: "Dashboard" }`) and `:30` (`{ href: "/sectors", label: "Sectors" }`) are persistent
  top-level sidebar links — **1 click** each (≤2 ✓). The sidebar was not modified this iteration (not
  in the diff), so no nav regression.
- **No duplicate home / no parallel shell.** Both pages render inside the existing shell
  (`PageHeading` + `Card` primitives); neither introduces its own layout/nav. No second "sectors" or
  "dashboard" surface was created.

---

## Part C — Advisory notes (WARN — do not block; for the decomposer to tidy next iteration)

1. **Breadth computing-module attribution drifts from the Data Contract (future-duplicate risk).**
   The blueprint registers "market breadth %" inside the **candidate-counts row** with computing
   module `app.engine.scanner:summarize_run` (blueprint line 66). iter-2 instead computes breadth
   inside `app.engine.regime:score_regime` (`regime.py:53-92`, `_universe_stats`) and serves it from
   the **canonical** `/api/dashboard` (`dashboard.py:36-41`). This is **not a violation today**: breadth
   is computed exactly once and served from the endpoint the contract names. But `summarize_run` does
   not exist yet (iter-5), and if iter-5 builds it to recompute breadth from setup statuses, that would
   create the exact "two sources for one number" the gate exists to prevent.
   - **Finite fix (decomposer, before iter-5):** amend the blueprint Data Contract so "market breadth %
     (above 50-/200-DMA)" records its canonical compute as `app.engine.regime:score_regime` and its
     serve as `/api/dashboard`; add the note that iter-5's `summarize_run` must **read** the regime's
     breadth, not recompute it.

2. **"Net new highs" dashboard metric is single-sourced but not granularly registered.** `/api/dashboard`
   serves `breadth.new_high_low` (net new-high/low, universe-relative) from `regime.py:162-168` — a real
   displayed value computed once in the regime engine and served via the canonical endpoint. It is part
   of the regime internals (which are registered) but is not enumerated as its own Data-Contract line.
   No divergence risk (single source). Per rule A5 this is an *unregistered-but-new* value → WARN.
   - **Finite fix (decomposer):** fold net-new-high/low under the regime row's registered internals
     (compute `app.engine.regime:score_regime`, serve `/api/dashboard`, labelled universe-relative).

Neither note is an objective Part A/Part B violation; both are recorded for tidy-up and do **not**
block the goal.

---

## Conclusion

The iteration that first engages the *Single source of truth* anti-goal kept the product coherent:
one computing module and one serving endpoint per canonical value, the Dashboard reusing
`/api/sectors` for Top Sectors, the frontend re-formatting only, and no nav/structure drift. Verdict
is **COHERENCE-WARN** solely for the two additive contract-reconciliation notes above (the breadth
attribution being the one with a real iter-5 duplicate risk if left unaddressed).
