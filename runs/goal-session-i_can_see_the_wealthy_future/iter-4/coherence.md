**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-4 (Stock Detail: chart + theme chips + invalidation, J-05)

- **Session:** i_can_see_the_wealthy_future
- **Iteration:** 4
- **Diff base (snapshot SHA):** `70fcc06a21042ff60686992ef16ac2abb8c128df` (matches recorded `iter-4/snapshot-sha`)
- **Auditor scope:** information architecture + data contract drift only (not code quality / not feature-works — those are reviewer/QA).

No objective Data-Contract or Information-Architecture violation found. All three new displayed
values were registered in the blueprint Data Contract **this iteration**, so not even an
"unregistered value" advisory applies. Clean PASS.

---

## Step 1 — Data Contract check (the "numbers don't match" gate)

The iteration's headline single-source risk — **the 50-DMA appears in three places** (chart overlay,
invalidation level, scoring extension/support) — is resolved by construction. All three derive from
the **one** canonical `app.engine.indicators:sma`:

- **`sma_series` reuses `sma`, not a second formula.** `indicators.py:29-37` —
  `[sma(values[: i + 1], period) for i in range(len(values))]`, so
  `sma_series(values, p)[-1] == sma(values, p)` holds by construction. One MA definition. ✅
- **Invalidation level uses the canonical `sma`.** `scoring.py:317-324` —
  `ind.sma(inv_closes, inv_period)` with `inv_period = cfg.decision_rules.invalidation.ma_period`
  (`scoring.py:232-234`). The human note string is built server-side in `_invalidation`
  (`scoring.py:203-212`); the frontend renders it **verbatim** (`page.tsx` `ThemeAndInvalidationCard`
  → `{row.invalidation.note}`). NA → `level: None` + honest "insufficient history" note, never
  fabricated. ✅
- **Chart `ma` series uses the canonical source.** `stocks.py:80` —
  `{str(period): sma_series(closes_asof, period) for period in cfg.indicators.ma_periods}`. Frontend
  `price-chart.tsx:107-124` **plots** `ma[period]` and **never computes a moving average from the
  close array** (confirmed by grep — no client-side MA math anywhere in `apps/frontend`). ✅

Registered-value tracing:

| Blueprint value | Canonical computer | Canonical endpoint | iter-4 conformance |
|---|---|---|---|
| Leadership / Entry Quality / Risk (per stock) | `app.engine.scoring:score_stocks` | `/api/stocks` + `/api/stocks/{ticker}` | **J-06 preserved.** Both routes go through `score_stocks` and the detail returns the *same row object* (`stocks.py:35-40`, comment "the SAME row object the leaderboard serves — never recomputed"). New `themes`+`invalidation` are appended to that shared row (`scoring.py:332-333`), so list==detail stays byte-identical. ✅ |
| Score breakdown + reason + **invalidation** | `score_stocks` via canonical `indicators:sma` (refined this iter) | same stock endpoints | Refinement registered in blueprint Data Contract (`blueprint.md` diff). Computed once; rides on shared row. ✅ |
| **Theme membership (per stock)** — NEW | `score_stocks` from `config.themes` map | rides on `/api/stocks` (+`/{ticker}`) | `scoring.py:268-274` reverses the **same** `cfg.themes` map `score_themes` ranks; names via the shared `theme_name(slug)` helper (`themes.py:34-38`, now used by both `score_themes` and `score_stocks` — a consolidation, not a fork). No second mapping. Registered. ✅ |
| **Price / MA / volume series** — NEW | `prices:bars_asof` (bars) + `indicators:sma_series` (MA) | `GET /api/stocks/{ticker}/bars` (NEW) | `stocks.py:44-81`: bars only via `bars_asof` (no-lookahead), `ma` keyed by every `config.indicators.ma_periods` entry. Own canonical endpoint, registered this iter. 503/404 honest. ✅ |

No new function recomputes a registered value via an independent path. No new UI surface fetches a
contract value from a non-canonical endpoint. No new displayed value duplicates an existing concept.
No unregistered value (the decomposer registered all three — Data Contract additions match the diff).
**No Step-1 violation.**

## Step 2 — Information Architecture check ("where do I find it / why is it everywhere")

- **No new route / no parallel shell.** The only changed frontend route is the existing
  `/stocks/[ticker]` (ui-surface-map: "New pages/routes: 0"). `PriceChart`, `ThemeAndInvalidationCard`,
  and `StockChartPanel` are added **inside** the existing `StockDetailBody` on `page.tsx` — they reuse
  the established `Card`/`PageHeading` shell, not a new layout. Stock Detail remains row-reached under
  the **Stocks** IA home, exactly as the blueprint specifies. ✅
- **`GET /api/stocks/{ticker}/bars`** is a backend API endpoint, not a navigable UI surface; it is
  consumed by `fetchStockBars` (`api.ts:200-203`) on the existing detail page — no nav path needed. ✅
- **Theme chips link to the existing home.** `page.tsx` `ThemeAndInvalidationCard` renders each chip as
  `<Link href="/themes">` — the canonical Themes home in the IA. No new route, no duplicate home. ✅
- **No nav-skeleton change** → correctly **no** `blueprint.reapproval-requested` written, matching the
  spec's Blueprint-conformance section.

**No Step-2 violation.**

## Step 3 — Subjective observations (advisory only)

- **Label consistency improved, not drifted.** Promoting `theme_name(slug)` into a shared helper
  (`themes.py:34-38`) means a theme reads identically on the `/themes` leaderboard and on a Stock
  Detail chip — this pre-empts the "same entity labelled differently" drift rather than introducing it.
- **Palette discipline.** `price-chart.tsx` reads colours from the same `globals.css` CSS tokens
  (`--accent`, `--pos`, `--neg`, `--border`, …) the rest of the workstation uses — no arbitrary hex;
  consistent with the established dark-workstation style.
- **Pre-existing, not iter-4:** `StockRow.rank: number` in `api.ts` while the backend appends
  `"rank": None` — unchanged by this iteration; out of scope for this gate. No action.

No advisory issue rises to a WARN.

## Supply-chain note (informational, not a coherence rule)

`lightweight-charts@5.2.0` is pinned in `package.json` and added to the npm allowlist
(`install-security-policy.json`) — confirms a **single** charting path (no second client-side chart/MA
library). Out of this gate's mandate, but consistent with single-source.

---

## Conclusion

**COHERENCE-PASS.** The one-MA-definition guarantee holds across all three displays of the 50-DMA;
invalidation + theme membership ride on the byte-identical shared `score_stocks` row served by both
canonical stock endpoints (J-06 intact); the new bars/MA series has its own registered canonical
endpoint; and the iteration adds no route, no parallel shell, and no duplicate home — theme chips link
to the existing `/themes`. All new contract values were registered in `blueprint.md` this iteration.
Nothing to consolidate next iteration.
