/**
 * Unit tests for the availability heatmap's calendar layout (lib/availability-month-bands.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/availability-month-bands.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-25-dev.md; `npx tsx lib/availability-month-bands.test.ts` is
 * the local fallback. These run in the CI/QA Node environment either way, same as every other
 * `lib/*.test.ts` file here.)
 *
 * The regression these pin: the previous layout emitted a leading blank offset for the 1st of the month
 * ONLY, then packed the trading-day cells consecutively into the 7-column Mo–Su grid. Every skipped
 * weekend or holiday therefore shifted every later day one column left — measured against the real
 * benchmark calendar, 14 of June 2026's 21 trading days rendered under the wrong weekday header, six of
 * them under "Sa"/"Su", making the grid look as though the availability payload contained weekend and
 * holiday dates. It never has: `compute_availability` emits one cell per benchmark (SPY) trading day,
 * and the stored SPY calendar contains zero weekend dates.
 *
 * The invariant every case below restates independently: a day slot's column (its index % 7) equals that
 * date's OWN Monday-first weekday index, computed here straight from `Date.getUTCDay()` rather than from
 * anything the module exports.
 */
import assert from "node:assert";

import { toMonthBands } from "./availability-month-bands.ts";
import type { MonthBand } from "./availability-month-bands.ts";
import type { AvailabilityCell } from "./api.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

function cell(date: string): AvailabilityCell {
  return { date, symbols_with_bars: 3, total_symbols: 158, snapshot_exists: false };
}

/** The real benchmark (SPY) trading days for a month, as stored — `days` are day-of-month numbers. */
function month(prefix: string, days: number[]): AvailabilityCell[] {
  return days.map((d) => cell(`${prefix}-${String(d).padStart(2, "0")}`));
}

/** Independent restatement of the Monday-first column a date BELONGS in (0 = Mon … 6 = Sun). */
function trueColumn(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7;
}

/** The grid column a date was actually PLACED in, or -1 when it is absent from the band. */
function renderedColumn(band: MonthBand, iso: string): number {
  const idx = band.slots.findIndex((s) => s.kind === "day" && s.cell.date === iso);
  return idx === -1 ? -1 : idx % 7;
}

function assertEveryDayAligned(band: MonthBand) {
  for (const [idx, slot] of band.slots.entries()) {
    if (slot.kind !== "day") continue;
    assert.strictEqual(
      idx % 7,
      trueColumn(slot.cell.date),
      `${slot.cell.date} rendered in column ${idx % 7}, belongs in ${trueColumn(slot.cell.date)}`,
    );
  }
}

// The real stored SPY calendar for three consecutive months (queried from apps/backend/data/trendora.db).
// June 2026 starts on a Monday and is missing Fri 2026-06-19 (Juneteenth).
const JUNE_DAYS = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16, 17, 18, 22, 23, 24, 25, 26, 29, 30];
// July 2026 starts mid-week (the 1st is a Wednesday) and is missing Fri 2026-07-03 (Independence Day
// observed — the 4th falls on a Saturday).
const JULY_DAYS = [1, 2, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31];
// August 2026 starts on a Saturday, so its first trading day is Mon the 3rd. Tue 2026-08-04 is a genuine
// intra-week gap in the stored data (not a holiday) — the layout must handle it identically.
const AUGUST_DAYS = [3, 5, 6, 7, 10, 11, 12, 13];

const JUNE = month("2026-06", JUNE_DAYS);
const JULY = month("2026-07", JULY_DAYS);
const AUGUST = month("2026-08", AUGUST_DAYS);

// --- 1. The regression itself: a month whose 1st IS a trading day still drifted after week one --------

check("June 2026: every trading day sits under its own weekday column", () => {
  const [band] = toMonthBands(JUNE);
  assertEveryDayAligned(band);
});

check("June 2026: Mon 06-08 is in the Monday column (it used to render under 'Sa')", () => {
  const [band] = toMonthBands(JUNE);
  assert.strictEqual(renderedColumn(band, "2026-06-08"), 0);
});

check("June 2026: no trading day is placed in the Sa/Su columns", () => {
  const [band] = toMonthBands(JUNE);
  const weekendPlaced = band.slots.filter((s, i) => s.kind === "day" && i % 7 >= 5);
  assert.deepStrictEqual(weekendPlaced, []);
});

// --- 2. A month starting mid-week -----------------------------------------------------------------------

check("July 2026 (the 1st is a Wednesday): every trading day is aligned", () => {
  const [band] = toMonthBands(JULY);
  assertEveryDayAligned(band);
  assert.strictEqual(renderedColumn(band, "2026-07-01"), 2); // Wed
  assert.strictEqual(renderedColumn(band, "2026-07-06"), 0); // Mon — used to render under "Fr"
});

// --- 3. A month starting on a weekend -------------------------------------------------------------------

check("August 2026 (the 1st is a Saturday): 7 leading blanks, Mon 08-03 at column 0", () => {
  const [band] = toMonthBands(AUGUST);
  const firstDay = band.slots.findIndex((s) => s.kind === "day");
  assert.strictEqual(firstDay, 7); // 5 offset blanks for Mo–Fr + the untraded Sat 1st and Sun 2nd
  assert.strictEqual(renderedColumn(band, "2026-08-03"), 0);
  assertEveryDayAligned(band);
});

check("August 2026: the intra-week gap on Tue 08-04 is a blank, and Wed 08-05 keeps its column", () => {
  const [band] = toMonthBands(AUGUST);
  assert.strictEqual(renderedColumn(band, "2026-08-04"), -1); // absent from the payload -> never drawn
  assert.strictEqual(band.slots[8].kind, "blank"); // the Tuesday position
  assert.strictEqual(renderedColumn(band, "2026-08-05"), 2); // Wed
});

// --- 4. A holiday inside a week ---------------------------------------------------------------------------

check("Juneteenth (Fri 2026-06-19) is a blank, and Mon 2026-06-22 still sits under Mo", () => {
  const [band] = toMonthBands(JUNE);
  assert.strictEqual(renderedColumn(band, "2026-06-19"), -1);
  const juneteenthSlot = band.slots[18]; // 0 leading blanks (the 1st is a Monday) + day 19 -> index 18
  assert.strictEqual(juneteenthSlot.kind, "blank");
  assert.strictEqual(18 % 7, trueColumn("2026-06-19")); // that blank IS the Friday position
  assert.strictEqual(renderedColumn(band, "2026-06-22"), 0);
});

// --- 5. Multi-month input ------------------------------------------------------------------------------------

check("consecutive months produce ascending bands with correct keys and labels", () => {
  const bands = toMonthBands([...JUNE, ...JULY, ...AUGUST]);
  assert.deepStrictEqual(
    bands.map((b) => b.key),
    ["2026-06", "2026-07", "2026-08"],
  );
  assert.deepStrictEqual(
    bands.map((b) => b.label),
    ["2026-06", "2026-07", "2026-08"],
  );
  for (const band of bands) assertEveryDayAligned(band);
});

// --- 6. No cell is lost, none is invented ------------------------------------------------------------------

check("every input cell appears exactly once, by reference, and none is fabricated", () => {
  const input = [...JUNE, ...JULY, ...AUGUST];
  const rendered = toMonthBands(input)
    .flatMap((b) => b.slots)
    .filter((s) => s.kind === "day");
  assert.strictEqual(rendered.length, input.length);
  assert.deepStrictEqual(
    rendered.map((s) => (s as { cell: AvailabilityCell }).cell),
    input,
  );
});

check("the day number carried on each slot matches its own date", () => {
  for (const band of toMonthBands([...JUNE, ...JULY, ...AUGUST])) {
    for (const slot of band.slots) {
      if (slot.kind !== "day") continue;
      assert.strictEqual(slot.day, Number(slot.cell.date.slice(8, 10)));
    }
  }
});

// --- 7. Empty input ------------------------------------------------------------------------------------------

check("an empty payload produces no bands (no fabricated month)", () => {
  assert.deepStrictEqual(toMonthBands([]), []);
});

console.log(`${passed} passed`);
