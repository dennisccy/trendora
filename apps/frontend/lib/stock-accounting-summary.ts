/**
 * goal-market-compass iter-40 (J-15) — pure disclosure-text helpers for the What-changed card's
 * stock-kind accounting (`compass-whatchanged-card.tsx`), extracted so the optional-field guard is
 * unit-testable under this project's plain-node convention (`node lib/stock-accounting-summary.test.ts`,
 * no test framework installed) — mirrors the `why-not-summary.ts` extraction from iter-39.
 *
 * `session_delta.stock_accounting` is OPTIONAL: absent on every `next_session_manifests` row frozen
 * before this field existed (never backfilled — AG-12). Both helpers return `null` for that case so the
 * card renders nothing new, never a crash and never a fabricated count (AG-8).
 *
 * `StockAccountingLike` mirrors `SessionDeltaStockAccounting` (lib/api.ts) as its OWN local type
 * (dependency-free, so this module runs under plain `node` without pulling in api.ts's fetch machinery).
 */
export interface StockAccountingLike {
  evaluated_count: number;
  shown_count: number;
  suppressed_count: number;
  residual_count: number;
}

/**
 * The residual disclosure — distinct text from the existing "Suppressed moves (N)" line (TC-4): an
 * above-threshold stock mover held back by the display cap is a DIFFERENT thing from a below-threshold
 * one, and the reader must be able to tell them apart. Renders even at `residual_count === 0` (an
 * explicit, honest zero — never a blank) whenever `stock_accounting` is present; `null` (render nothing)
 * only when the field itself is absent (TC-5).
 */
export function stockResidualDisclosureText(stockAccounting?: StockAccountingLike): string | null {
  if (stockAccounting === undefined) {
    return null;
  }
  const n = stockAccounting.residual_count;
  return `${n} more stock move${n === 1 ? "" : "s"} held back by the display cap`;
}

/**
 * The "showing top N" disclosure beside the shown stock entries (TC-4b, goal text step 4) — only when
 * the display cap actually held something back this session (`residual_count > 0`); omitted entirely
 * when `residual_count === 0` or `stock_accounting` is absent, so an unbounded session shows no
 * unnecessary caveat.
 */
export function stockShownCapDisclosureText(stockAccounting?: StockAccountingLike): string | null {
  if (stockAccounting === undefined || stockAccounting.residual_count === 0) {
    return null;
  }
  const n = stockAccounting.shown_count;
  return `Showing the top ${n} stock move${n === 1 ? "" : "s"}`;
}
