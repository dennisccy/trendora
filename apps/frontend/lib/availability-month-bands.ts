import type { AvailabilityCell } from "./api";

/**
 * The single, pure authority for how `AvailabilityHeatmap`
 * (`components/availability-heatmap.tsx`) lays the per-trading-date cells out into its month-banded,
 * Monday-first 7-column calendar grid. No React, no DOM types, so it is unit-testable under `node` —
 * the existing frontend convention (see `lib/availability-empty-state.ts`, consumed by the same
 * component).
 *
 * The layout walks EVERY calendar day of each month and emits a slot for it — a `day` slot when the
 * payload has a cell for that date, a `blank` otherwise. That is what keeps each cell under its own
 * weekday column, and it is why the fix lives here rather than in the component.
 *
 * The bug it replaces: the previous version emitted a leading blank offset for the 1st of the month
 * ONLY, then packed the trading-day cells consecutively into the 7-column grid. Because non-trading days
 * are simply absent from the payload, every skipped weekend or holiday shifted every later day one
 * column left — a drift of +2 columns per week that wrapped every 3.5 weeks, so part of each month
 * realigned by coincidence and the grid still read as a plausible calendar. Measured against the real
 * benchmark calendar, 14 of June 2026's 21 trading days landed under the wrong weekday header and six
 * of them under "Sa"/"Su" — which made the heatmap look as though the availability payload contained
 * weekend and holiday dates. It never has: `compute_availability`
 * (`apps/backend/app/engine/data_manager.py`) emits exactly one cell per benchmark (SPY) trading day,
 * and the stored SPY calendar holds zero weekend dates. The cells were always honest; only their
 * positions were fabricated.
 *
 * Non-trading days deliberately render as NOTHING (an empty grid position) rather than as a styled
 * "market closed" placeholder — the heatmap's density scale already uses a dark bucket 0 for a real
 * trading day with zero bars, and a dimmed placeholder beside it would blur that distinction.
 */

export type MonthSlot =
  /** An empty grid position — a non-trading day (weekend / holiday) or a leading offset. Rendered as
   *  nothing at all, so it can never be mistaken for a real zero-coverage trading day. */
  | { kind: "blank" }
  /** A trading day with an availability cell. `day` is the day-of-month, precomputed so the component
   *  never re-parses a date during render. */
  | { kind: "day"; cell: AvailabilityCell; day: number };

export type MonthBand = {
  key: string; // yyyy-MM
  label: string; // "2026-05"
  /** The grid positions for this month, in render order. Index % 7 is the Monday-first column. */
  slots: MonthSlot[];
};

/** Monday-based weekday index (0 = Mon … 6 = Sun) — calendar grids start the week on Monday. */
function mondayIndex(dt: Date): number {
  return (dt.getUTCDay() + 6) % 7;
}

/** Days in the given UTC month (`month0` is 0-based) — day 0 of the NEXT month is the last of this one.
 *  The same idiom `components/asof-calendar.tsx` already uses to build its month grid. */
function daysInMonthUTC(year: number, month0: number): number {
  return new Date(Date.UTC(year, month0 + 1, 0)).getUTCDate();
}

/** Group the ascending availability cells by `yyyy-MM`, preserving order. */
function groupByMonth(cells: AvailabilityCell[]): { key: string; cells: AvailabilityCell[] }[] {
  const groups: { key: string; cells: AvailabilityCell[] }[] = [];
  let current: { key: string; cells: AvailabilityCell[] } | null = null;
  for (const cell of cells) {
    const key = cell.date.slice(0, 7);
    if (!current || current.key !== key) {
      current = { key, cells: [] };
      groups.push(current);
    }
    current.cells.push(cell);
  }
  return groups;
}

/**
 * Lay the ascending availability cells out into one month band per `yyyy-MM`, each a flat list of grid
 * slots in render order (index % 7 == the Monday-first column).
 *
 * Placement is provable rather than incidental: the leading offset is `mondayIndex(the 1st)` and every
 * calendar day thereafter contributes exactly one slot, so day `d` sits at index
 * `mondayIndex(1st) + d - 1`, whose column is identically `mondayIndex(d)`. A gap of any length — a
 * weekend, a market holiday, or a multi-week hole in the stored data — travels through the same branch
 * and cannot shift a later day.
 */
export function toMonthBands(cells: AvailabilityCell[]): MonthBand[] {
  return groupByMonth(cells).map((group) => {
    const year = Number(group.key.slice(0, 4));
    const month0 = Number(group.key.slice(5, 7)) - 1;

    const byDay = new Map<number, AvailabilityCell>();
    for (const cell of group.cells) byDay.set(Number(cell.date.slice(8, 10)), cell);

    const slots: MonthSlot[] = [];
    for (let i = mondayIndex(new Date(Date.UTC(year, month0, 1))); i > 0; i -= 1) {
      slots.push({ kind: "blank" });
    }
    for (let day = 1; day <= daysInMonthUTC(year, month0); day += 1) {
      const cell = byDay.get(day);
      slots.push(cell ? { kind: "day", cell, day } : { kind: "blank" });
    }
    return { key: group.key, label: group.key, slots };
  });
}
