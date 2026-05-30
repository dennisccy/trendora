**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-5 (Scanner snapshots + Scanner Runs)

- **Session:** i_can_see_the_wealthy_future
- **Iteration:** 5 — immutable as-of scanner-run history (J-07, J-08)
- **Audited against:** `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.md`
- **Diff base:** `git diff f808f8d6d725f08bb9898988a1c88652ad445d53` (+ uncommitted/untracked)
- **Date:** 2026-05-30

This iteration added the persistence spine — append-only `scanner_runs` / `scanner_results` /
`sector_scores` / `theme_scores` tables, `app.engine.scanner:run_scan` + `bootstrap_runs`, the
`GET /api/runs` (+ `/{run_id}`) endpoints, and two frontend pages that graduate from EmptyState
stubs. No objective Data-Contract or Information-Architecture violation found. This was the
iteration the spec itself flagged as "the one place to get single-source wrong," and the code
avoided it cleanly.

## Part A — Data Contract (the "numbers don't match" gate) → PASS

The spec's single-source liability (carried forward from the iter-2 coherence lesson): `run_scan`'s
summary must **read** the canonical breadth / new-high-low / candidate counts, never recompute them
from a second formula. Verified directly in the diff:

- `apps/backend/app/engine/scanner.py:65-71` — each canonical engine is called **exactly once** for
  `asof` (`score_regime`, `score_sectors`, `score_themes`, `score_stocks`), and
  `candidate_counts = summarize_candidates(stock_result["rows"])` reads the **registered canonical
  derivation** (`app.engine.setups:summarize_candidates`) over the canonical `score_stocks` rows.
- `scanner.py:81-84` — `breadth_above_50dma`, `breadth_above_200dma`, `new_high_low_json` are read
  straight from `regime[...]` (the `score_regime` output). **No second formula.** This is exactly
  the recompute the spec warned about, and it was avoided.
- `scanner.py:89-142` — per-stock / sector / theme child rows are stored as **faithful copies** of
  the canonical outputs (`record_json = json.dumps(row)` keeps the complete `score_stocks` row dict
  losslessly; typed columns mirror the canonical shapes). Nothing is re-derived.

**Serving stays single-source.** `apps/backend/app/api/runs.py:50-85` serves the **stored** snapshot
only — `rows = [json.loads(result.record_json) ...]` rehydrates the canonical `StockRow`; the regime
panel / breadth / counts come from the stored `ScannerRun` columns. It never calls a live `score_*`
engine for a historical run (the precise immutability bug J-08 guards against). `404`/`503` are
honest no-fabrication states.

**New entity is registered.** The blueprint Data Contract already carries the **"Scanner run
snapshot (list + detail)"** row (blueprint.md:77) → computed by `app.engine.scanner:run_scan`, served
by `GET /api/runs` + `GET /api/runs/{run_id}`, with the iter-5 serving note (blueprint.md:89). The
diff matches the contract module/endpoint paths exactly — no unregistered-value WARN needed.

**Frontend re-formats only.** `lib/api.ts:248-282` — `fetchRuns()`/`fetchRun()` hit the two
canonical endpoints and re-format; no score/bucket/return is computed client-side. The detail page
(`scanner-runs/[runId]/page.tsx`) renders the single `RunDetail` payload and **reuses** the shared
`ScoreBadge` / `ComponentBreakdown` / `Badge` components (same as the live leaderboard), so a stored
row reads identically to `/stocks`. No existing contract value gained a second source; the live
endpoints (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/bars`) are untouched
(per OUT OF SCOPE) — J-01–J-06 cannot regress from a coherence standpoint.

## Part B — Information Architecture (the "where do I find it" gate) → PASS

Two new surfaces: `/scanner-runs` (list) and `/scanner-runs/[runId]` (detail).

- **Canonical home + nav path.** Both already live under the blueprint's **Scanner Runs** IA section
  (blueprint.md:34-35, 50-51). `components/sidebar.tsx:31` carries the top-level link
  `{ href: "/scanner-runs", label: "Scanner Runs" }` → list reachable in **1 click**.
- **Detail reachability (≤2 clicks).** `/scanner-runs/[runId]` is **row-reached** via
  `scanner-runs/page.tsx:99-104` (`<Link href={`/scanner-runs/${run.run_id}`}>` on the as-of date) —
  2 clicks total (sidebar → list → row), exactly as the blueprint prescribes ("Run Detail — opened
  from a run row, not the top nav"). A back-link "All runs" → `/scanner-runs` exists
  (`[runId]/page.tsx:74-80`).
- **No parallel shell / no duplicate home.** Both pages use the existing app shell + shared
  components (`PageHeading`, `Card`, `EmptyState`, `Badge`, `ScoreBadge`, `ComponentBreakdown`); they
  **replace the iter-1 EmptyState stubs at the same routes**, so no second home for an existing
  entity and no invented nav. No nav-skeleton change → the spec correctly wrote no
  `blueprint.reapproval-requested`.

## Part C — Advisory (non-blocking)

- **None material.** Label/colour helpers are consistent with the rest of the app: `setupVariant`
  ("Actionable" → ok) mirrors the live Stock Leaderboard, and `regimeVariant` matches the Dashboard's
  regime colouring (both noted in-code). No value is formatted divergently across pages that I can
  point at.
- Minor (not a coherence issue, noted for completeness): `[runId]/page.tsx:161` formats
  `new_high_low.net_pct` directly while the DMA tiles use the `fmtPct` null-guard — safe because
  `net_pct` is typed non-null, and it's a single display, not a cross-page divergence.

## Conclusion

No Part A or Part B objective violation. The new snapshot entity is registered, computed by one
canonical module, served from its canonical endpoints as a stored copy, and displayed in its
blueprint IA home reachable in ≤2 clicks with no parallel shell. **COHERENCE-PASS.**
