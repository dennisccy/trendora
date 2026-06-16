/**
 * The single, locale-proof date-presentation authority for the whole frontend (J-42 / Capability 35).
 *
 * Every user-facing calendar date in Trendora renders `yyyy-MM-dd` through this one module — no
 * component holds a per-component date-format literal and nothing renders a date through a
 * locale-dependent path (no `toLocaleDateString`, no native `<input type="date">` widget output).
 *
 * Backend ISO date strings (the canonical contract) are already `yyyy-MM-dd`; the frontend NEVER
 * changes the API/DB/config date shape — this module only RE-FORMATS what the backend serves and
 * VALIDATES what the user types. `ISO_DATE_FORMAT` is the one shared constant; `formatIsoDate()` is
 * the one shared formatter; `isValidIsoDate()` is the one shared validator the `/data` text inputs use.
 */

/** The one displayed date format token (lowercase `yyyy-MM-dd`, e.g. `2026-05-01`). One source of truth. */
export const ISO_DATE_FORMAT = "yyyy-MM-dd" as const;

/**
 * The single URL query key that serializes the ONE global as-of state (J-43). One name, one owner —
 * defined here (a server/edge-safe, dependency-free module) so the App-Router middleware (J-83, Edge
 * runtime) and the client `asof-provider` (the sole `?asof` reader/writer) share the SAME literal with
 * no `"use client"` import and no second param name. Changing the param is a one-line edit here.
 */
export const ASOF_PARAM = "asof" as const;

/**
 * The request header the J-83 middleware forwards the shape-valid `?asof` value on, so the server-component
 * root layout can seed `AsOfProvider` with the SAME as-of the client will read from the URL — eliminating
 * the SSR/client hydration mismatch (server's lazy initializer otherwise sees no `window`). Forwarding
 * ONLY this one header for ONLY a shape-valid date keeps the asof-provider the sole `?asof` owner and
 * never leaks a provider key or any other query param into a header.
 */
export const ASOF_HEADER = "x-asof" as const;

/** Placeholder shown for an absent date (e.g. an empty coverage range). */
export const ISO_DATE_PLACEHOLDER = "yyyy-MM-dd" as const;

/** What `formatIsoDate(null)` / an unparseable value renders — a single em dash, never a fabricated date. */
const EMPTY = "—";

/** Strict `yyyy-MM-dd` shape: exactly 4-2-2 digits. Rejects `10/06/2026`, `2026-5-1`, `2026/05/01`. */
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

/**
 * True iff `value` is an exact `yyyy-MM-dd` string that is ALSO a real calendar date.
 *
 * Rejects the two error cases the `/data` inputs must reject:
 *   - `2026-13-40` — exact shape but month 13 / day 40 are not a real date.
 *   - `10/06/2026` — not `yyyy-MM-dd` shape at all.
 * A round-trip through `Date.UTC` catches calendar overflow (e.g. `2026-02-30` → March, so `getUTCDate`
 * no longer equals 30) without any locale dependence.
 */
export function isValidIsoDate(value: string): boolean {
  if (!ISO_DATE_RE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  if (month < 1 || month > 12 || day < 1 || day > 31) return false;
  const dt = new Date(Date.UTC(year, month - 1, day));
  // Round-trip: an overflowed date (e.g. Feb 30) normalises to a different y/m/d.
  return (
    dt.getUTCFullYear() === year &&
    dt.getUTCMonth() === month - 1 &&
    dt.getUTCDate() === day
  );
}

/**
 * The one formatter every surface uses to display a calendar date as `yyyy-MM-dd`.
 *
 * Backend dates are already ISO `yyyy-MM-dd` (possibly carrying a time suffix, e.g. an ISO datetime
 * `2026-05-01T13:30:00`), so this normalises to the date part and re-asserts the ISO shape through one
 * module — making this file the single format authority even where the backend value is "already ISO".
 * It performs NO locale formatting and NO timezone shift: it slices/validates the string, never routes
 * through `Date.toLocaleDateString`. An empty / unparseable value renders the em-dash placeholder
 * (never a fabricated date).
 */
export function formatIsoDate(value: string | null | undefined): string {
  if (!value) return EMPTY;
  // Take the date portion of an ISO datetime ("2026-05-01T..." or "2026-05-01 13:30") — date-only authority.
  const datePart = value.slice(0, 10);
  return isValidIsoDate(datePart) ? datePart : EMPTY;
}

/**
 * Format an ISO datetime (`yyyy-MM-ddTHH:mm:ss…`) as `yyyy-MM-dd HH:mm:ss` — the displayed-timestamp
 * counterpart of `formatIsoDate`, used where a run/scan timestamp (not just a date) is shown. Same
 * authority, same locale-proof guarantee: it slices the ISO string, never routes through a locale path.
 */
export function formatIsoDateTime(value: string | null | undefined): string {
  if (!value) return EMPTY;
  const datePart = value.slice(0, 10);
  if (!isValidIsoDate(datePart)) return EMPTY;
  const timePart = value.slice(11, 19); // HH:mm:ss, if present
  return timePart ? `${datePart} ${timePart}` : datePart;
}
