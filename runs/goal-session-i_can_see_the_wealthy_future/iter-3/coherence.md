**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_can_see_the_wealthy_future-iter-3

- **Session:** i_can_see_the_wealthy_future · **Iteration:** 3 (Per-stock scores + theme scores → Stock & Theme Leaderboards + dashboard rollup)
- **Audited against snapshot:** `970d1ba` — this is a `WIP on goal/...` stash-style commit taken *after* the iteration ran, so `git diff 970d1ba` shows only trace/telemetry. The iteration's real changes are uncommitted vs HEAD (`1157f47`, the pre-iter-3 merge), so this audit used `git diff HEAD` + the untracked new files (the standard fallback).
- **Blueprint:** `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`
- **UI surface map:** present (`reports/phase-goal-i_can_see_the_wealthy_future-iter-3-ui-surface-map.md`)

## One-line summary

No objective Data-Contract or Information-Architecture violations. The three per-stock scores, the
theme score, the setup status, and the candidate counts are each computed in **exactly one** engine
module and served from **exactly one** canonical path; `/api/stocks` and `/api/stocks/{ticker}` read
the *same* `score_stocks` row (the J-06 single-source proof — the iteration's headline risk); the
frontend recomputes nothing. The iteration additionally **closed both iter-2 WARN notes** (breadth
re-attributed to the regime engine; the private `_label_for` import replaced by a shared
`labels.py`). **COHERENCE-PASS** with one optional, non-blocking observation.

---

## Part A — Data Contract check (the "numbers don't match" gate)

**Result: no FAIL.** Single source of truth holds for every value displayed this iteration.

| Registered value | Canonical compute (blueprint) | Found compute site (sole) | Canonical serve | Found serve | OK? |
|---|---|---|---|---|---|
| Leadership / Entry Quality / Risk (per stock) | `app.engine.scoring:score_stocks` | `apps/backend/app/engine/scoring.py:212` | `/api/stocks` **+** `/api/stocks/{ticker}` (same computation) | `app/api/stocks.py:26` (list) and `:34-39` (filters the **same** result) | ✅ |
| Theme score | `app.engine.themes:score_themes` | `apps/backend/app/engine/themes.py:81` | `GET /api/themes` | `app/api/themes.py:26` (verbatim) | ✅ |
| Setup status (per stock) | `app.engine.setups:classify_setup` | `apps/backend/app/engine/setups.py:48` | rides on the stock rows | `scoring.py:287` (one call site) | ✅ |
| Candidate counts (# Actionable / Breakout-watch / Pullback-watch) | `app.engine.setups:summarize_candidates` | `apps/backend/app/engine/setups.py:73` | `GET /api/dashboard` | `app/api/dashboard.py:38` counts `score_stocks(...).rows` | ✅ |
| A–E bucket | `app.engine.buckets:to_bucket` | `buckets.py` (only deriver) | rides on each score | `scoring.py:285`, `themes.py:148` call it | ✅ |
| Market breadth % + net new-high/low | `app.engine.regime:score_regime` (re-attributed iter-3) | `regime.py` (only site) | `GET /api/dashboard` | `dashboard.py` breadth block **unchanged** — read, not recomputed | ✅ |
| score→label (regime/sector/theme trend) | `app.engine.labels:label_for` (iter-3 consolidation) | `labels.py:14` (single def) | rides on each score | `regime.py:124`, `sectors.py:127`, `themes.py:154` all import it | ✅ |

Evidence the single-source rule held:

- **J-06 — the iteration's central risk — is structurally guaranteed.** `score_stocks`
  (`scoring.py:212`) is the only producer of the three per-stock scores. `/api/stocks/{ticker}`
  (`stocks.py:34-39`) calls that **same** producer and *filters its rows* for the ticker, returning the
  identical row object the leaderboard serves — it does **not** recompute per-ticker. NVDA's
  scores/buckets on list and detail are produced by byte-identical code → cannot diverge.
- **Macro context is read, never recomputed.** `score_stocks` reads the canonical regime once
  (`scoring.py:221`, `score_regime`) and the canonical sector ranking once (`scoring.py:224`,
  `score_sectors`) to build its contextual Risk components — these are *inputs read from the canonical
  computation*, not second computations or second serving paths. No duplicate `score_regime` /
  `_compute_*` / second sharpe-style function exists in the diff.
- **Candidate counts have one derivation.** `summarize_candidates` (`setups.py:73`) is the sole place
  counts are produced — it *counts* the canonical per-stock setup statuses; `dashboard.py:38` feeds it
  `score_stocks(...).rows`. The dashboard counts and the `/api/stocks` setup statuses therefore come
  from the one `score_stocks → classify_setup` path.
- **Setup status has one classifier with the critical gate.** `classify_setup` (`setups.py:48`) is the
  only classifier; the Risk-off gate is the first branch (`setups.py:57-58` → `Risk-off-watchlist`,
  zero Actionable). Called once per row (`scoring.py:287`).
- **Theme score has exactly one serving path.** `score_themes` (`themes.py:81`) → `/api/themes`
  (`themes.py:26`). The Dashboard's **Top Themes** does **not** re-serve it: `dashboard.py` removed the
  old `top_themes` placeholder entirely, and `app/page.tsx:58,115` calls `fetchThemes()` → `/api/themes`
  and slices `rows.slice(0, 5)` — exactly the proven Top-Sectors pattern. Basket-return math is shared
  (`scoring.py` imports `themes.basket_return`/`total_return`, `scoring.py:43`), so a theme's basket
  return has one definition.
- **A–E derived in one place.** `to_bucket` is the sole bucketer (called at `scoring.py:285`,
  `themes.py:148`). The frontend `ScoreBadge` receives the **server** `bucket` letter as a prop and the
  `invert` flag flips only the *colour* — "The bucket LETTER is unchanged" (`score-badge.tsx` docstring;
  `bucketVariant(bucket, invert)`). No client-side bucket derivation.
- **Frontend re-formats only.** `lib/api.ts` is fetch + typed re-format ("NO business computation here",
  `api.ts:1-6`). `/stocks` filtering is client-side display only (`stocks/page.tsx:74` "never re-sorts
  or recomputes a score"); the lone `.sort()` (`:70`) orders the **sector-name dropdown list**, not
  scores. `ComponentBreakdown` change adds only key→human-label strings. No score/return arithmetic in
  the frontend diff — only `.toFixed()` formatting.
- **iter-2 WARN notes resolved (the gate's loop closing).** The blueprint edit this iteration is
  additive: it re-attributes "market breadth % + net new-high/low" to `regime:score_regime` and
  candidate counts to `setups:summarize_candidates` (away from the not-yet-existing
  `scanner:summarize_run`), with explicit "iter-5 must READ, not recompute" notes — exactly the finite
  fixes prescribed in iter-2's WARN. The code matches the reconciled contract. The function-name
  alignments (`score_stock`→`score_stocks`, `score_theme`→`score_themes`) are clarifications, not a new
  source. No IA row was modified; no Data-Contract row gained a second source.

---

## Part B — Information Architecture check (the "where do I find it" gate)

**Result: no FAIL.** Zero new routes; all four surfaces are existing blueprint IA homes.

- `/`, `/stocks`, `/themes` are pre-existing IA homes. `/stocks` and `/themes` are **1-click**
  persistent top-level sidebar links (`components/sidebar.tsx:28` and `:29`). The sidebar was **not
  modified** this iteration (not in the diff) → no nav regression and no nav-skeleton change.
- **Stock Detail is correctly row-reached, not nav-listed.** `/stocks/[ticker]` is intentionally absent
  from the nav (blueprint: "opened from a leaderboard row, not the nav"). It is reachable in **2 clicks**
  via the row ticker link `href={`/stocks/${row.ticker}`}` (`stocks/page.tsx:188-189`), and provides a
  "Back to leaderboard" return + an unknown-ticker link back to `/stocks` (`stocks/[ticker]/page.tsx:63-67,80`).
- **No duplicate home / no parallel shell.** All four pages render inside the shared root layout's
  `<Sidebar/>` + main area; none defines its own layout or nav. No second "stocks"/"themes"/"dashboard"
  surface was created. `ui/select.tsx` is a new shared form primitive, not a route.
- **No reapproval needed and none requested.** `blueprint.reapproval-requested` is correctly absent
  (no nav change), matching the spec.

---

## Part C — Advisory (non-blocking; optional future tidy)

1. **Three percentile-normalization copies (intentional, documented; not a contract value).**
   `cross_sectional_percentiles` (`engine/normalize.py`) is now shared by `scoring.py` and `themes.py`,
   but `sectors.py` deliberately keeps its own copy ("to avoid touching J-04 math", `normalize.py:6`).
   This is a pure internal-math helper, **not** a registered displayed value, so it is *not* a
   Data-Contract violation and does not affect any served number. Noted only as an optional later
   consolidation once J-04's output is locked in by snapshot tests — entirely non-blocking.

---

## Conclusion

The second and harder live test of *Single source of truth* (J-06) was met by construction:
`/api/stocks` and `/api/stocks/{ticker}` filter the *same* `score_stocks` computation, candidate
counts count those same rows, the theme score has one producer and one serving path with the dashboard
slicing it client-side, and the shared `label_for`/`to_bucket` are the sole derivers. The frontend
re-formats only, the nav skeleton is unchanged with every surface in its blueprint home, and the
blueprint edit was an additive reconciliation that **resolved both outstanding iter-2 WARN notes**.
Verdict is **COHERENCE-PASS**.
