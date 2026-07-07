/**
 * iter-19 — the honest "Unassigned" bucket for a stock with no mapped GICS sector.
 *
 * The broadened 30-year / 548-name pool (iter-18) made `StockRow.sector` genuinely nullable: ~78% of
 * pool names have no entry in `config.stock_sectors` (the mapping only covers a curated subset), so the
 * backend honestly serves `sector: null` rather than fabricating a GICS sector (goal.md anti-goal —
 * never invent data). This module is the ONE place that maps that null to a display/filter/sort value —
 * used by the leaderboard's sector filter + comparator, and by every page that displays a stock's sector
 * (stock detail, scanner-run detail) — so "Unassigned" reads identically everywhere, never a blank cell
 * or a literal "null" string.
 */

/** The honest bucket label for a stock with no mapped GICS sector. Never fabricates a real sector. */
export const UNASSIGNED_SECTOR = "Unassigned";

/** The sector's display/filter/sort label: the real GICS sector name, or the honest `UNASSIGNED_SECTOR`
 *  bucket. One mapping shared by display cells, the filter vocabulary, and the sort comparator below. */
export function sectorLabel(sector: string | null): string {
  return sector ?? UNASSIGNED_SECTOR;
}

/** Null-safe ascending sector comparator: an unmapped ("Unassigned") sector sorts deterministically
 *  alongside its peers instead of throwing when `.localeCompare` is called against `null`. */
export function compareSectors(a: string | null, b: string | null): number {
  return sectorLabel(a).localeCompare(sectorLabel(b));
}
