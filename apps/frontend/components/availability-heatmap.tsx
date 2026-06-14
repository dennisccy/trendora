"use client";

import { useCallback, useMemo, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/empty-state";
import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";
import type { AvailabilityCell, AvailabilityResponse } from "@/lib/api";

/**
 * J-61 — the per-trading-date availability heatmap on `/data`.
 *
 * READ-ONLY presentation of the `GET /api/data/availability` payload (one cell per benchmark trading
 * day): a month-banded calendar grid colored by `symbols_with_bars` density (a sequential ramp), a
 * distinct ring marker on days that also have an immutable snapshot, a legend, and exact figures on
 * hover (date, symbols-with-bars / total, snapshot yes/no). A SPARSE day (e.g. 3-of-158) is visually
 * distinct from a FULL day; a low-coverage day is visibly muted. All dates render `yyyy-MM-dd` via the
 * shared `formatIsoDate` (J-42).
 *
 * Clicking a day, or shift-clicking a second day to select a range, calls `onPrefillRange(start, end)`
 * — the page wires that into the JOB FORM's Start/End inputs. These are JOB PARAMETERS, NEVER the global
 * as-of viewing control (J-18): this component never touches `setAsOf`. The density→color mapping is pure
 * frontend presentation (no numeric classification is sent to or computed by the backend; no config knob).
 *
 * iter-5 nested-interactive guard: each day is a single `<button>` (the click target); the snapshot
 * marker and the hover tooltip are non-interactive `<span>`s INSIDE it — no nested interactive element.
 */

type DensityBucket = 0 | 1 | 2 | 3 | 4 | 5;

/** Map a day's coverage fraction (symbols_with_bars / total_symbols) to a 6-step density bucket. Pure
 *  presentation — a frontend-only sequential ramp; no magic number reaches the backend derivation. A
 *  zero-coverage day is bucket 0 (visibly empty); a fully-covered day is bucket 5. */
function densityBucket(withBars: number, total: number): DensityBucket {
  if (total <= 0 || withBars <= 0) return 0;
  const frac = withBars / total;
  if (frac >= 1) return 5;
  if (frac >= 0.75) return 4;
  if (frac >= 0.5) return 3;
  if (frac >= 0.25) return 2;
  return 1;
}

/** The sequential color ramp (low → full). A muted surface for empty/sparse, an increasingly saturated
 *  accent for denser coverage — so a sparse 3-of-158 day reads clearly fainter than a full day. */
const BUCKET_CLASS: Record<DensityBucket, string> = {
  0: "bg-surface-2 border border-border",
  1: "bg-accent/15 border border-accent/20",
  2: "bg-accent/30 border border-accent/30",
  3: "bg-accent/50 border border-accent/40",
  4: "bg-accent/70 border border-accent/50",
  5: "bg-accent border border-accent",
};

/** Per-bucket day-number text token (design tokens only — NO hardcoded hex). The faint/low buckets (0–3)
 *  sit on dark or low-opacity-accent backgrounds, so the day number must be the high-contrast `text-text`
 *  (near-white) to stay legible — the old `text-text-muted` rendered dark-on-dark on buckets 0–1. The
 *  bright buckets (4–5) are saturated teal, so dark `text-bg` reads clearly on them. */
const BUCKET_TEXT_CLASS: Record<DensityBucket, string> = {
  0: "text-text",
  1: "text-text",
  2: "text-text",
  3: "text-text",
  4: "text-bg",
  5: "text-bg",
};

const LEGEND: { bucket: DensityBucket; label: string }[] = [
  { bucket: 0, label: "none" },
  { bucket: 1, label: "<25%" },
  { bucket: 2, label: "25–50%" },
  { bucket: 3, label: "50–75%" },
  { bucket: 4, label: "75–<100%" },
  { bucket: 5, label: "full" },
];

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] as const;

/** Parse a `yyyy-MM-dd` cell date into a UTC Date (no locale/timezone shift — matches lib/dates). */
function parseIsoUTC(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

/** Monday-based weekday index (0 = Mon … 6 = Sun) — calendar grids start the week on Monday. */
function mondayIndex(dt: Date): number {
  return (dt.getUTCDay() + 6) % 7;
}

type MonthBand = {
  key: string; // yyyy-MM
  label: string; // "2026-05"
  leadingBlanks: number; // empty grid slots before the first day of the month
  cells: AvailabilityCell[]; // the trading-day cells in this month, ascending
};

/** Group the ascending availability cells into month bands, each with the leading-blank offset so the
 *  first day lands under its real weekday column. Only trading days are rendered (non-trading days are
 *  simply absent — honest: the grid shows what the calendar has, never a fabricated cell). */
function toMonthBands(cells: AvailabilityCell[]): MonthBand[] {
  const bands: MonthBand[] = [];
  let current: MonthBand | null = null;
  for (const cell of cells) {
    const dt = parseIsoUTC(cell.date);
    const key = cell.date.slice(0, 7); // yyyy-MM
    if (!current || current.key !== key) {
      const firstOfMonth = new Date(Date.UTC(dt.getUTCFullYear(), dt.getUTCMonth(), 1));
      current = { key, label: key, leadingBlanks: mondayIndex(firstOfMonth), cells: [] };
      bands.push(current);
    }
    current.cells.push(cell);
  }
  return bands;
}

export function AvailabilityHeatmap({
  state,
  selectedStart,
  selectedEnd,
  onPrefillRange,
}: {
  state:
    | { kind: "loading" }
    | { kind: "error" }
    | { kind: "ok"; data: AvailabilityResponse };
  /** The current job-form Start/End (so the heatmap highlights the prefilled selection). */
  selectedStart?: string;
  selectedEnd?: string;
  /** Prefill the JOB FORM's Start/End from a clicked day (start == end) or a shift-click range. NEVER the
   *  global as-of control. */
  onPrefillRange: (start: string, end: string) => void;
}) {
  // Hover tooltip: the cell currently hovered/focused (exact figures shown for it). Non-interactive.
  const [hovered, setHovered] = useState<AvailabilityCell | null>(null);
  // Shift-click range anchor: the first day of an in-progress range selection.
  const [anchor, setAnchor] = useState<string | null>(null);

  // Month bands DESCENDING (newest month first, top→bottom) so the most recent history is visible without
  // scrolling. Each month's INTERNAL day order stays ascending (a calendar reads left→right, top→bottom).
  const bands = useMemo(
    () =>
      state.kind === "ok" ? toMonthBands(state.data.cells).slice().reverse() : [],
    [state],
  );

  const handleDayClick = useCallback(
    (cell: AvailabilityCell, shiftKey: boolean) => {
      if (shiftKey && anchor) {
        // Complete a range: order the two endpoints ascending and prefill [start, end].
        const [start, end] = anchor <= cell.date ? [anchor, cell.date] : [cell.date, anchor];
        onPrefillRange(start, end);
        setAnchor(null);
      } else {
        // A plain click selects a single day (start == end) and arms it as a range anchor.
        setAnchor(cell.date);
        onPrefillRange(cell.date, cell.date);
      }
    },
    [anchor, onPrefillRange],
  );

  const inSelectedRange = useCallback(
    (iso: string) => {
      if (!selectedStart || !selectedEnd) return false;
      const lo = selectedStart <= selectedEnd ? selectedStart : selectedEnd;
      const hi = selectedStart <= selectedEnd ? selectedEnd : selectedStart;
      return iso >= lo && iso <= hi;
    },
    [selectedStart, selectedEnd],
  );

  return (
    <Card className="p-0" data-testid="availability-heatmap">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">Per-date availability</h2>
        </div>
        <p className="mt-0.5 text-xs text-text-faint">
          For each benchmark trading day: how many symbols have a bar (the cell density) and whether an
          immutable snapshot exists (the ring). Descriptive metadata read from the dataset — not a
          recomputed score. Click a day to prefill the job dates below; shift-click a second day for a
          range. (These are job parameters — they never change the global as-of date.)
        </p>
      </div>

      {state.kind === "loading" ? (
        <div className="flex items-center gap-2 p-6 text-sm text-text-muted" data-testid="availability-loading">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Loading availability…
        </div>
      ) : null}

      {state.kind === "error" ? (
        <div className="p-4">
          <p className="text-sm text-text-muted" data-testid="availability-error">
            Availability could not load from the API. No cells are shown rather than fabricated values.
          </p>
        </div>
      ) : null}

      {state.kind === "ok" && state.data.cells.length === 0 ? (
        <div className="p-4">
          <EmptyState
            icon={CalendarDays}
            title="No availability yet"
            description="There are no stored trading days to chart. Fetch real EOD prices to populate the dataset, then the per-date availability appears here."
          />
        </div>
      ) : null}

      {state.kind === "ok" && state.data.cells.length > 0 ? (
        <div className="space-y-4 p-4">
          {/* Legend + hovered-day exact figures */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2" data-testid="availability-legend">
              <span className="text-xs text-text-faint">Coverage</span>
              <div className="flex items-center gap-1">
                {LEGEND.map(({ bucket, label }) => (
                  <span key={bucket} className="flex items-center gap-1" title={label}>
                    <span className={cn("h-3 w-3 rounded-sm", BUCKET_CLASS[bucket])} aria-hidden />
                    <span className="text-[10px] text-text-faint">{label}</span>
                  </span>
                ))}
              </div>
              <span className="ml-2 flex items-center gap-1 text-[10px] text-text-faint">
                <span className="relative inline-flex h-3 w-3 items-center justify-center" aria-hidden>
                  <span className="h-3 w-3 rounded-sm bg-accent/50 ring-2 ring-pos ring-offset-0" />
                </span>
                snapshot
              </span>
            </div>

            {/* The exact figures for the hovered/focused day — read verbatim from the cell, no recompute. */}
            <div className="num text-xs text-text-muted" aria-live="polite" data-testid="availability-hover-readout">
              {hovered ? (
                <span>
                  <span className="text-text">{formatIsoDate(hovered.date)}</span>
                  {" · "}
                  <span className="text-text">
                    {hovered.symbols_with_bars}/{hovered.total_symbols}
                  </span>{" "}
                  symbols ·{" "}
                  {hovered.snapshot_exists ? (
                    <span className="text-pos">snapshot yes</span>
                  ) : (
                    <span className="text-text-faint">snapshot no</span>
                  )}
                </span>
              ) : (
                <span className="text-text-faint">Hover or focus a day for exact figures</span>
              )}
            </div>
          </div>

          {/* Month-banded calendar grid (weeks as rows, Monday-first). Two month bands per row on a normal
              viewport (collapsing to one column on narrow screens) so more history is visible without
              excessive scrolling. Scrolls within the card on a tall history; never truncates a covered day. */}
          <div className="grid max-h-[28rem] grid-cols-1 gap-x-5 gap-y-5 overflow-auto pr-1 md:grid-cols-2">
            {bands.map((band) => (
              <div key={band.key} data-testid="availability-month" data-month={band.label}>
                <div className="mb-1 num text-xs font-medium text-text-muted">{band.label}</div>
                <div className="grid grid-cols-7 gap-1">
                  {WEEKDAYS.map((w) => (
                    <div key={w} className="text-center text-[10px] text-text-faint">
                      {w}
                    </div>
                  ))}
                  {Array.from({ length: band.leadingBlanks }).map((_, i) => (
                    <span key={`blank-${i}`} aria-hidden />
                  ))}
                  {band.cells.map((cell) => {
                    const dt = parseIsoUTC(cell.date);
                    const bucket = densityBucket(cell.symbols_with_bars, cell.total_symbols);
                    const selected = inSelectedRange(cell.date);
                    const isAnchor = anchor === cell.date;
                    return (
                      <button
                        key={cell.date}
                        type="button"
                        data-testid="availability-cell"
                        data-date={cell.date}
                        data-bucket={bucket}
                        data-symbols={cell.symbols_with_bars}
                        data-total={cell.total_symbols}
                        data-snapshot={cell.snapshot_exists ? "yes" : "no"}
                        data-selected={selected ? "yes" : "no"}
                        aria-pressed={selected}
                        aria-label={`${cell.date}: ${cell.symbols_with_bars} of ${cell.total_symbols} symbols, snapshot ${cell.snapshot_exists ? "yes" : "no"}`}
                        title={`${cell.date} · ${cell.symbols_with_bars}/${cell.total_symbols} symbols · snapshot ${cell.snapshot_exists ? "yes" : "no"}`}
                        onMouseEnter={() => setHovered(cell)}
                        onMouseLeave={() => setHovered((h) => (h?.date === cell.date ? null : h))}
                        onFocus={() => setHovered(cell)}
                        onBlur={() => setHovered((h) => (h?.date === cell.date ? null : h))}
                        onClick={(e) => handleDayClick(cell, e.shiftKey)}
                        className={cn(
                          "relative flex h-7 items-center justify-center rounded-sm text-[10px] font-medium tabular-nums transition",
                          BUCKET_CLASS[bucket],
                          BUCKET_TEXT_CLASS[bucket],
                          "hover:brightness-110 hover:ring-1 hover:ring-accent",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                          (selected || isAnchor) && "ring-2 ring-accent ring-offset-1 ring-offset-surface",
                          // the snapshot ring marker — a positive-toned ring distinct from the selection ring
                          cell.snapshot_exists && !selected && !isAnchor && "ring-2 ring-pos",
                        )}
                      >
                        {/* the day-of-month number — non-interactive text inside the single button */}
                        <span aria-hidden>{dt.getUTCDate()}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <p className="border-t border-border pt-2 text-[11px] text-text-faint">
            Cell density = symbols with a bar on that day ÷ total stored symbols ({state.data.total_symbols}).
            A sparser day is fainter; a day with an immutable snapshot carries a ring. A trading day with no
            non-benchmark bars is shown honestly (low/empty), never omitted as if covered.
          </p>
        </div>
      ) : null}
    </Card>
  );
}
