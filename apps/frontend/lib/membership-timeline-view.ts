/**
 * J-99 — pure client-side VIEW TRANSFORMS for the dynamic-universe membership timeline.
 *
 * The Data Manager `/data` membership-timeline panel (J-96, `MembershipTimelinePanel`) serves the canonical
 * `membership_timeline.points` payload — one object per snapshot date, each carrying the stored J-93/J-94
 * `size`, `entries`, `exits`, and `excluded` counts. These helpers add pagination (10 rows/page, newest-
 * first) and Year/Month dropdown filters as a PURE view transform: they only `filter`/`slice`/`reverse`
 * over the served objects and NEVER re-derive, sum, or restate any per-date value (Single source of truth;
 * No recompute in the read path). Every row returned is a verbatim reference into the input `points` array.
 *
 * This is the same view-transform contract the leaderboard sort/search/filter (J-48/J-55/J-56/J-64) and the
 * per-symbol coverage table already follow. The Year/Month selectors are LIST controls — they are NOT the
 * global as-of switcher and introduce NO date state (J-18, critical).
 */
import type { MembershipTimelinePoint } from "./api";

/** Rows shown per page in the membership-timeline table. A single named constant — never an inline literal
 *  scattered through the render (iter-20 no-magic-numbers spirit; mirrors the J-48/J-64 view-transform
 *  controls). */
export const MEMBERSHIP_TIMELINE_PAGE_SIZE = 10;

/** The "All" sentinel value for the Year/Month dropdowns — selecting it matches every date. */
export const ALL_SENTINEL = "__all__";

/** Distinct calendar years present in the payload, newest-first (for the Year dropdown options). */
export function deriveYearOptions(points: MembershipTimelinePoint[]): string[] {
  const years = new Set<string>();
  for (const p of points) years.add(p.date.slice(0, 4));
  return Array.from(years).sort((a, b) => b.localeCompare(a)); // newest year first
}

/** Distinct months (MM, ascending) present in the payload, optionally constrained to a selected year.
 *  When `year` is the ALL sentinel, returns every month present across the whole payload. */
export function deriveMonthOptions(points: MembershipTimelinePoint[], year: string): string[] {
  const months = new Set<string>();
  for (const p of points) {
    if (year !== ALL_SENTINEL && p.date.slice(0, 4) !== year) continue;
    months.add(p.date.slice(5, 7));
  }
  return Array.from(months).sort((a, b) => a.localeCompare(b));
}

/** Select EXACTLY the points whose ISO date matches the chosen Year and Month. An ALL sentinel on either
 *  axis is a wildcard. The returned array holds the SAME object references as the input (verbatim subset,
 *  no recomputation) and preserves the input order. */
export function filterTimelinePoints(
  points: MembershipTimelinePoint[],
  year: string,
  month: string,
): MembershipTimelinePoint[] {
  return points.filter((p) => {
    if (year !== ALL_SENTINEL && p.date.slice(0, 4) !== year) return false;
    if (month !== ALL_SENTINEL && p.date.slice(5, 7) !== month) return false;
    return true;
  });
}

export interface TimelinePage {
  /** The <=PAGE_SIZE rows for this page, newest-first (a verbatim slice of the input). */
  rows: MembershipTimelinePoint[];
  /** The clamped 1-based page index actually shown. */
  page: number;
  /** Total number of pages — `max(1, ceil(total / PAGE_SIZE))`. */
  pageCount: number;
  /** Total number of dates in the (already-filtered) input set. */
  total: number;
  /** True when the filtered set has zero rows (drives the honest empty state — never a fabricated row). */
  isEmpty: boolean;
}

/**
 * Page the (already-filtered) points newest-first, 10 per page. The requested `page` is clamped to
 * `[1, pageCount]` so an out-of-range request never renders a fabricated/blank row. The input is assumed
 * oldest-first (as `membership_timeline.points` serves it); the output is reversed to newest-first, exactly
 * the order the J-96 table renders today (`points.slice().reverse()`).
 */
export function paginateTimelinePoints(
  filtered: MembershipTimelinePoint[],
  page: number,
): TimelinePage {
  const total = filtered.length;
  const pageCount = Math.max(1, Math.ceil(total / MEMBERSHIP_TIMELINE_PAGE_SIZE));
  const clamped = Math.min(Math.max(1, Math.trunc(page)), pageCount);
  const newestFirst = filtered.slice().reverse(); // verbatim references, newest date first
  const start = (clamped - 1) * MEMBERSHIP_TIMELINE_PAGE_SIZE;
  const rows = newestFirst.slice(start, start + MEMBERSHIP_TIMELINE_PAGE_SIZE);
  return { rows, page: clamped, pageCount, total, isEmpty: total === 0 };
}
