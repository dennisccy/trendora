"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";

/**
 * J-62 — the as-of calendar popover BODY (month grid). A pure RENDERER of the single global as-of
 * control: the available snapshot `dates` (from `asof-provider`) are the selectable days; every other
 * day is disabled; "Latest" returns to the latest view. Selecting a day calls `onSelect(date | null)`,
 * which the switcher wires straight to the existing `setAsOf` — so this component holds NO second date
 * state. The only local state is the VIEWED MONTH (a UI navigation cursor — which month panel is on
 * screen), which is not an as-of value and never serializes anywhere.
 *
 * Month navigation spans the stored history: the left/right arrows clamp to the oldest and newest stored
 * months (you can always reach the oldest stored month). Fully keyboard operable: the month-nav buttons,
 * "Latest", and each selectable day are real `<button>`s in tab order; arrows + Enter operate them; the
 * parent closes the popover on Escape / outside-click and on a selection.
 *
 * Dates render `yyyy-MM-dd` via the shared formatter (J-42). All date math is UTC (no locale/timezone
 * shift), matching `lib/dates`.
 */

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] as const;

function parseIsoUTC(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

/** A `yyyy-MM` month key for a Date (UTC). */
function monthKey(year: number, month0: number): string {
  return `${year}-${String(month0 + 1).padStart(2, "0")}`;
}

/** Monday-based weekday index (0 = Mon … 6 = Sun). */
function mondayIndex(dt: Date): number {
  return (dt.getUTCDay() + 6) % 7;
}

export function AsOfCalendar({
  dates,
  latest,
  asOf,
  onSelect,
  onClose,
}: {
  /** All available snapshot dates, DESCENDING (newest first) — the only selectable days. */
  dates: string[];
  /** The latest available date (the "Latest" target == clearing the as-of). */
  latest: string | null;
  /** The current selection (null when viewing the latest). Drives the highlighted day — NOT a second state. */
  asOf: string | null;
  /** Select a snapshot date, or null for "Latest". The switcher passes this straight to `setAsOf`. */
  onSelect: (date: string | null) => void;
  /** Dismiss the popover (Escape / a selection / outside click handled by the parent). */
  onClose: () => void;
}) {
  // The set of selectable days + the min/max stored months (the navigation bounds).
  const selectable = useMemo(() => new Set(dates), [dates]);
  const sortedAsc = useMemo(() => [...dates].sort(), [dates]);
  const oldest = sortedAsc[0] ?? null;
  const newest = sortedAsc[sortedAsc.length - 1] ?? null;

  // The viewed month is a UI navigation cursor (NOT an as-of value): default to the month of the current
  // selection, else the latest stored month. Held as {year, month0}.
  const initial = useMemo(() => {
    const anchor = asOf ?? latest ?? newest;
    const dt = anchor ? parseIsoUTC(anchor) : new Date();
    return { year: dt.getUTCFullYear(), month0: dt.getUTCMonth() };
  }, [asOf, latest, newest]);
  const [view, setView] = useState(initial);

  const containerRef = useRef<HTMLDivElement>(null);
  // Move focus into the popover on open so it is immediately keyboard operable.
  useEffect(() => {
    const first = containerRef.current?.querySelector<HTMLElement>("[data-autofocus]");
    first?.focus();
  }, []);

  const viewKey = monthKey(view.year, view.month0);
  const oldestKey = oldest ? oldest.slice(0, 7) : viewKey;
  const newestKey = newest ? newest.slice(0, 7) : viewKey;
  const canPrev = viewKey > oldestKey; // can still reach an older stored month
  const canNext = viewKey < newestKey;

  function stepMonth(delta: number) {
    setView((v) => {
      const dt = new Date(Date.UTC(v.year, v.month0 + delta, 1));
      return { year: dt.getUTCFullYear(), month0: dt.getUTCMonth() };
    });
  }

  // Build the day grid for the viewed month: a leading blank offset so day 1 lands under its weekday.
  const firstOfMonth = new Date(Date.UTC(view.year, view.month0, 1));
  const daysInMonth = new Date(Date.UTC(view.year, view.month0 + 1, 0)).getUTCDate();
  const leadingBlanks = mondayIndex(firstOfMonth);
  const dayCells = Array.from({ length: daysInMonth }, (_, i) => {
    const day = i + 1;
    const iso = `${monthKey(view.year, view.month0)}-${String(day).padStart(2, "0")}`;
    return { day, iso, selectable: selectable.has(iso) };
  });

  // Keyboard: Escape closes; ArrowLeft/Right move months (when the focus isn't on a day, the parent's
  // day buttons handle their own focus order naturally via Tab).
  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
    }
  }

  return (
    <div
      ref={containerRef}
      role="dialog"
      aria-label="Choose as-of date"
      data-testid="asof-calendar"
      onKeyDown={onKeyDown}
      className="w-72 rounded-md border border-border bg-surface p-3 shadow-lg"
    >
      {/* Month navigation header */}
      <div className="mb-2 flex items-center justify-between">
        <button
          type="button"
          aria-label="Previous month"
          data-testid="asof-cal-prev"
          disabled={!canPrev}
          onClick={() => stepMonth(-1)}
          className={cn(
            "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border text-text-muted transition",
            "hover:border-border-strong hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            "disabled:cursor-not-allowed disabled:opacity-40",
          )}
        >
          <ChevronLeft className="h-4 w-4" aria-hidden />
        </button>
        <span className="num text-sm font-medium text-text" data-testid="asof-cal-month">
          {viewKey}
        </span>
        <button
          type="button"
          aria-label="Next month"
          data-testid="asof-cal-next"
          disabled={!canNext}
          onClick={() => stepMonth(1)}
          className={cn(
            "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border text-text-muted transition",
            "hover:border-border-strong hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            "disabled:cursor-not-allowed disabled:opacity-40",
          )}
        >
          <ChevronRight className="h-4 w-4" aria-hidden />
        </button>
      </div>

      {/* Weekday header */}
      <div className="mb-1 grid grid-cols-7 gap-1">
        {WEEKDAYS.map((w) => (
          <div key={w} className="text-center text-[10px] text-text-faint">
            {w}
          </div>
        ))}
      </div>

      {/* Day grid: selectable snapshot days are buttons; others are muted, disabled placeholders. */}
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: leadingBlanks }).map((_, i) => (
          <span key={`blank-${i}`} aria-hidden />
        ))}
        {dayCells.map((cell) => {
          const isSelected = asOf === cell.iso;
          const isLatest = latest === cell.iso;
          if (!cell.selectable) {
            return (
              <span
                key={cell.iso}
                aria-disabled
                data-testid="asof-cal-day-disabled"
                className="flex h-8 items-center justify-center rounded-sm text-xs text-text-faint/40"
              >
                {cell.day}
              </span>
            );
          }
          return (
            <button
              key={cell.iso}
              type="button"
              data-testid="asof-cal-day"
              data-date={cell.iso}
              data-selected={isSelected ? "yes" : "no"}
              aria-pressed={isSelected}
              aria-label={`View as-of ${cell.iso}${isLatest ? " (latest)" : ""}`}
              title={formatIsoDate(cell.iso)}
              onClick={() => {
                onSelect(isLatest ? null : cell.iso);
                onClose();
              }}
              className={cn(
                "flex h-8 items-center justify-center rounded-sm text-xs tabular-nums transition",
                "border border-accent/30 bg-accent/10 text-text",
                "hover:bg-accent hover:text-bg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                isSelected && "bg-accent text-bg ring-2 ring-accent ring-offset-1 ring-offset-surface",
              )}
            >
              {cell.day}
            </button>
          );
        })}
      </div>

      {/* "Latest" affordance — returns to the latest view (clears the as-of). */}
      <div className="mt-3 flex items-center justify-between border-t border-border pt-2">
        <span className="text-[10px] text-text-faint">
          {dates.length} selectable date{dates.length === 1 ? "" : "s"}
        </span>
        <button
          type="button"
          data-autofocus
          data-testid="asof-cal-latest"
          onClick={() => {
            onSelect(null);
            onClose();
          }}
          className={cn(
            "inline-flex h-7 items-center gap-1.5 rounded-md border px-2.5 text-xs font-medium transition",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            asOf === null
              ? "border-accent bg-surface-2 text-accent"
              : "border-border bg-surface-2 text-text-muted hover:border-border-strong hover:text-text",
          )}
        >
          <Clock className="h-3.5 w-3.5" aria-hidden />
          Latest{latest ? ` · ${formatIsoDate(latest)}` : ""}
        </button>
      </div>
    </div>
  );
}
