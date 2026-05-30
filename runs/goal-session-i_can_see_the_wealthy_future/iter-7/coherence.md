**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-7 (Watchlist with persistence, J-11)

**Session:** i_can_see_the_wealthy_future · **Iteration:** 7 · **Auditor:** coherence-auditor
**Snapshot audited:** `git diff a18fc2da3d027341e4295ff350b7350826fecc5d` + uncommitted (`git status`)
**Result:** No objective Data-Contract or Information-Architecture violation. One advisory note only.

This is the goal-completing iteration and the **first user-write surface** that *displays canonical
scores* — the single-source risk the iter-2/J-06 lesson exists to catch. It is handled correctly.

---

## Step 1 — Data Contract (the "numbers don't match" gate) → PASS

Blueprint canonical sources in play: per-stock Leadership/Entry/Risk + A–E bucket + setup +
invalidation = `app.engine.scoring:score_stocks` served by `GET /api/stocks`; price-since-added =
`app.engine.prices:close_on`.

- **Scores/bucket/setup/invalidation read, never recomputed.** `watchlist.py:53` calls
  `score_stocks(session, asof, cfg)` with `asof = latest_data_date(session)` and copies the fields
  **verbatim** (`watchlist.py:81-82`, `_CANONICAL_FIELDS`). `stocks.py:27` serves the **identical**
  call — `score_stocks(session, latest_data_date(session), get_config())`. Same module, same as-of,
  same row → the watchlist's "current" values are byte-identical to `/api/stocks` (J-06 now holds on
  a write surface). No new function computes a score/bucket/setup/invalidation anywhere in the diff.
  Confirmed by the new guard `test_single_source_equals_stocks_row_byte_for_byte`
  (`test_api_watchlist.py:90`, asserts `entry[key] == stock_row[key]` for each canonical field).
- **No persisted-then-drifting copy.** The `Watchlist` table (`models.py:228+`) stores ONLY
  `{ticker, reason, created_at, asof_date_added, entry_close}` — no score column. A stored score
  would be a second source; it does not exist.
- **price_since_added is the registered canonical derivation.** `_price_since_added`
  (`watchlist.py:57-66`) = `close_on(session, ticker, asof) / entry_close − 1`, i.e. the canonical
  price series ÷ the captured `entry_close`. This is exactly the refined blueprint Watchlist row, and
  it is not recomputed in the UI (the frontend only formats it via `fmtPct`/`priceClass`,
  `page.tsx:27-39`). `None`→"NA" and 0.0→"+0.00%" are honest, non-fabricated states. Not one of the
  six scores; not a re-derivation of any registered value.
- **Frontend recomputes nothing.** `page.tsx` and `api.ts` only re-format the one `/api/watchlist`
  payload (badges, %, colour). `WatchlistEntry` (`api.ts`) carries the server `ScoreBlock`/`setup`/
  `invalidation` straight through to `ScoreBadge`/`Badge`. No client-side score, bucket, MA, or
  return math.
- **Blueprint refinement is additive and consistent.** The pre-existing Watchlist Data-Contract row
  was sharpened from the vague "reuses stored `scanner_results` + `app.engine.indicators`" to name
  the exact sources (`score_stocks` read live; `close_on`). The implementation matches the refined
  row, and reading live `score_stocks` is the **stronger** single-source choice (it is literally the
  `/api/stocks` path, not a parallel snapshot read). No new/duplicate registered value introduced.

## Step 2 — Information Architecture (the "where do I find it" gate) → PASS

- **Canonical home, already in the skeleton.** `/watchlist` is the blueprint IA home for J-11. The
  page graduates the existing stub in place — no parallel route invented.
- **Reachable in 1 click.** `apps/frontend/components/sidebar.tsx:33` —
  `{ href: "/watchlist", label: "Watchlist", icon: Star }` is a top-level persistent sidebar link.
  Statically verified; not hidden, not >2 clicks.
- **No parallel shell.** The page renders inside the standard app shell and reuses
  `PageHeading`/`Card`/`EmptyState`/`ScoreBadge`/`Badge` — no bespoke nav/layout.
- **No duplicate home.** The per-row ticker link targets the existing canonical Stock Detail home
  `/stocks/[ticker]` (`page.tsx:249`); it does not create a second stock page.
- **No nav-skeleton change** → correctly no `blueprint.reapproval-requested`. The only blueprint edit
  is the additive Data-Contract row refinement + the iter-7 serving note.

## Scope containment (J-01–J-10 cannot regress)

The diff is purely additive: a new `Watchlist` table appended after `ForwardReturn` (no existing
table mutated), one router registration (`main.py`), new `api/watchlist.py`, new client helpers, the
page, and tests. **No** existing engine module (`scanner/scoring/regime/sectors/themes/setups/
buckets/forward_testing/prices`) and **no** live endpoint (`dashboard/stocks/sectors/themes/runs/
system-health/bars`) was touched — no canonical value re-pointed to a new code path.

## Step 3 — Advisory (non-blocking)

- **(WARN, cosmetic)** `setupVariant` in `page.tsx:41-56` maps a setup *status string* → a Badge
  colour client-side. The status text itself is the server's verbatim value (`entry.setup.status`),
  so this is **presentation styling, not a displayed data value** — not a single-source violation. If
  an equivalent status→colour map also lives on `/stocks`, a future tidy could lift it into one
  shared helper for visual consistency. Advisory only; no action required this iteration.

---

**No COHERENCE-FAIL conditions present.** No duplicate computation, no non-canonical source, no
unregistered displayed value, no hidden/duplicate/undiscoverable route, no parallel shell. Verdict:
**COHERENCE-PASS.**
