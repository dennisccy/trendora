/**
 * Unit tests for the J-99 pure membership-timeline view transforms (lib/membership-timeline-view.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/membership-timeline-view.test.ts
 *
 * The J-99 crux (Single source of truth / No recompute in the read path): the rendered page must be a
 * VERBATIM slice/filter of the served `timeline.points`. These tests assert that:
 *   (a) Year/Month filtering selects EXACTLY the dates whose ISO date matches (no recomputation);
 *   (b) pagination yields <=10 rows/page newest-first and pageCount === ceil(filteredCount/10);
 *   (c) the filtered+paged rows are the SAME object references from the input (no per-date size/entries/
 *       exits/excluded value is re-derived) — a verbatim subset;
 *   (d) an empty filter combination yields zero rows + isEmpty true, never a fabricated row;
 *   (e) an out-of-range page clamps to bounds (never a fabricated/blank row).
 */
import assert from "node:assert";

import {
  MEMBERSHIP_TIMELINE_PAGE_SIZE,
  ALL_SENTINEL,
  deriveYearOptions,
  deriveMonthOptions,
  filterTimelinePoints,
  paginateTimelinePoints,
} from "./membership-timeline-view.ts";
import type { MembershipTimelinePoint } from "./api.ts";

// A small synthetic timeline spanning two years and several months, oldest-first as the payload serves it.
function pt(date: string, size: number): MembershipTimelinePoint {
  return { date, size, entries: [], exits: [], excluded: { below_history: 0, below_price: 0, below_adv: 0 } };
}

// 25 points: 2024 (Jan x3, Feb x2), 2025 (Mar x20) — enough to exercise multi-page pagination.
const POINTS: MembershipTimelinePoint[] = [
  pt("2024-01-05", 10),
  pt("2024-01-12", 11),
  pt("2024-01-19", 12),
  pt("2024-02-02", 13),
  pt("2024-02-09", 14),
  ...Array.from({ length: 20 }, (_, i) => pt(`2025-03-${String(i + 1).padStart(2, "0")}`, 100 + i)),
];

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- the page size is a named constant, not a magic literal -------------------------------------

check("MEMBERSHIP_TIMELINE_PAGE_SIZE is 10", () => {
  assert.strictEqual(MEMBERSHIP_TIMELINE_PAGE_SIZE, 10);
});

// --- option derivation: distinct calendar values present in the payload --------------------------

check("deriveYearOptions returns the distinct years present, newest-first", () => {
  assert.deepStrictEqual(deriveYearOptions(POINTS), ["2025", "2024"]);
});

check("deriveYearOptions on an empty payload returns no years", () => {
  assert.deepStrictEqual(deriveYearOptions([]), []);
});

check("deriveMonthOptions (no year filter) returns distinct months present, ascending", () => {
  // months present across the whole payload: 01, 02 (2024), 03 (2025)
  assert.deepStrictEqual(deriveMonthOptions(POINTS, ALL_SENTINEL), ["01", "02", "03"]);
});

check("deriveMonthOptions constrained to a year returns only that year's months", () => {
  assert.deepStrictEqual(deriveMonthOptions(POINTS, "2024"), ["01", "02"]);
  assert.deepStrictEqual(deriveMonthOptions(POINTS, "2025"), ["03"]);
});

// --- filtering selects EXACTLY the matching ISO dates, verbatim ----------------------------------

check("filter with both ALL sentinels returns every point unchanged (same references)", () => {
  const out = filterTimelinePoints(POINTS, ALL_SENTINEL, ALL_SENTINEL);
  assert.strictEqual(out.length, POINTS.length);
  out.forEach((p, i) => assert.strictEqual(p, POINTS[i], "verbatim same reference, no recompute"));
});

check("filter by year selects exactly the dates whose ISO year matches", () => {
  const out2024 = filterTimelinePoints(POINTS, "2024", ALL_SENTINEL);
  assert.deepStrictEqual(
    out2024.map((p) => p.date),
    ["2024-01-05", "2024-01-12", "2024-01-19", "2024-02-02", "2024-02-09"],
  );
  // verbatim: same object refs, no size/entries/exits/excluded re-derived
  out2024.forEach((p) => assert.ok(POINTS.includes(p), "verbatim subset reference"));
});

check("filter by year+month selects exactly the matching ISO year-month", () => {
  const out = filterTimelinePoints(POINTS, "2024", "01");
  assert.deepStrictEqual(out.map((p) => p.date), ["2024-01-05", "2024-01-12", "2024-01-19"]);
});

check("filter by month only (ALL years) selects that month across years", () => {
  const out = filterTimelinePoints(POINTS, ALL_SENTINEL, "02");
  assert.deepStrictEqual(out.map((p) => p.date), ["2024-02-02", "2024-02-09"]);
});

check("an empty filter combination yields zero rows (honest empty, never fabricated)", () => {
  // 2025 has only month 03 → asking for 2025-01 matches nothing
  const out = filterTimelinePoints(POINTS, "2025", "01");
  assert.deepStrictEqual(out, []);
});

// --- pagination: <=10 rows/page, newest-first, ceil(count/10) pages, clamped ---------------------

check("paginate page 1 yields the 10 NEWEST dates, newest-first", () => {
  const r = paginateTimelinePoints(POINTS, 1);
  assert.strictEqual(r.rows.length, 10);
  assert.strictEqual(r.pageCount, 3); // 25 points / 10 → 3 pages
  assert.strictEqual(r.page, 1);
  assert.strictEqual(r.total, 25);
  // newest-first: the very newest date in the payload leads page 1
  assert.strictEqual(r.rows[0].date, "2025-03-20");
  assert.strictEqual(r.rows[9].date, "2025-03-11");
});

check("paginate page 2 yields the next 10 older dates (distinct from page 1)", () => {
  const p1 = paginateTimelinePoints(POINTS, 1);
  const p2 = paginateTimelinePoints(POINTS, 2);
  assert.strictEqual(p2.rows.length, 10);
  assert.strictEqual(p2.rows[0].date, "2025-03-10");
  // page 1 and page 2 share no dates → a differential, non-identical slice
  const p1Dates = new Set(p1.rows.map((p) => p.date));
  p2.rows.forEach((p) => assert.ok(!p1Dates.has(p.date), "page 2 disjoint from page 1"));
});

check("paginate last page yields the remaining (<=10) oldest dates", () => {
  const r = paginateTimelinePoints(POINTS, 3);
  assert.strictEqual(r.rows.length, 5); // 25 - 20 = 5
  assert.strictEqual(r.rows[r.rows.length - 1].date, "2024-01-05"); // the OLDEST date is last
});

check("paginated rows are verbatim object references (no recomputation)", () => {
  const r = paginateTimelinePoints(POINTS, 1);
  r.rows.forEach((p) => assert.ok(POINTS.includes(p), "verbatim same reference"));
});

check("an out-of-range page clamps to the last page (never a fabricated/blank row)", () => {
  const r = paginateTimelinePoints(POINTS, 999);
  assert.strictEqual(r.page, 3); // clamped to pageCount
  assert.strictEqual(r.rows.length, 5);
  r.rows.forEach((p) => assert.ok(POINTS.includes(p), "no fabricated row"));
});

check("a page below 1 clamps to page 1", () => {
  const r = paginateTimelinePoints(POINTS, 0);
  assert.strictEqual(r.page, 1);
  assert.strictEqual(r.rows[0].date, "2025-03-20");
});

check("an empty filtered set paginates to zero rows, pageCount 1, isEmpty true", () => {
  const r = paginateTimelinePoints([], 1);
  assert.deepStrictEqual(r.rows, []);
  assert.strictEqual(r.pageCount, 1);
  assert.strictEqual(r.total, 0);
  assert.strictEqual(r.isEmpty, true);
});

check("a non-empty page is not flagged empty", () => {
  const r = paginateTimelinePoints(POINTS, 1);
  assert.strictEqual(r.isEmpty, false);
});

console.log(`\nmembership-timeline-view: ${passed} checks passed`);
