"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";
import { resolveStep } from "@/lib/asof-step";

/**
 * J-62 — the as-of calendar popover BODY (month grid). A pure RENDERER of the single global as-of
 * control: the available snapshot `dates` (from `asof-provider`) are the selectable days; every other
 * day is disabled; "Latest" returns to the latest view. Selecting a day calls `onSelect(date | null)`,
 * which the switcher wires straight to the existing `setAsOf` — so this component holds NO second date
 * state. The only local state is the VIEWED MONTH (a UI navigation cursor — which month panel is on
 * screen), which is not an as-of value and never serializes anywhere.
 *
 * Month navigation spans the stored history: the left/right month-nav buttons clamp to the oldest and
 * newest stored months (you can always reach the oldest stored month). Fully keyboard operable: the
 * month-nav buttons, "Latest", and each selectable day are real `<button>`s in tab order; Enter operates
 * them; the parent closes the popover on Escape / outside-click and on a selection.
 *
 * J-71 — ArrowLeft / ArrowRight on the open popover SCRUB the single global as-of one AVAILABLE snapshot
 * date at a time (older / newer), live, via the existing `onSelect`→`setAsOf` — bounded at the oldest and
 * newest (newest == "Latest", i.e. `onSelect(null)`). The popover stays OPEN while scrubbing; only Escape /
 * a day click / a click outside close it. The viewed-month cursor follows the landing date. This adds NO
 * second date state and uses NO global window/document listener — it lives on this dialog's `onKeyDown`
 * (the dialog is focused on open via `data-autofocus`), preserving the J-18 single-global-as-of invariant.
 *
 * J-79 — the header also gains Year + Month quick-jump dropdowns that move the VIEWED MONTH cursor only
 * (a presentation aid, NOT a second date state), so the user can jump months without clicking chevrons.
 * The selectable-day / disabled-day / "Latest" / Escape / click-to-commit affordances are unchanged.
 *
 * Dates render `yyyy-MM-dd` via the shared formatter (J-42). All date math is UTC (no locale/timezone
 * shift), matching `lib/dates`.
 */

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] as const;

/** Month labels for the J-79 month-jump dropdown (index 0 = January), display-only — no locale path. */
const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
] as const;

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

  // J-79 — the Year / Month quick-jump dropdowns. They navigate the VIEWED MONTH ONLY (a presentation
  // cursor, exactly like the chevrons) — NOT a second date state, never serialized, never an as-of value.
  // Year options span the stored history (oldest..newest stored year); months are all twelve. A chosen
  // (year, month) is CLAMPED to the stored [oldestKey, newestKey] range so the cursor can't leave the
  // navigable history (mirroring the chevrons' clamp), and it selects nothing — it only moves which month
  // panel is on screen; the user still clicks a selectable day to commit a date.
  const oldestYear = oldest ? Number(oldest.slice(0, 4)) : view.year;
  const newestYear = newest ? Number(newest.slice(0, 4)) : view.year;
  const yearOptions = Array.from({ length: newestYear - oldestYear + 1 }, (_, i) => oldestYear + i);

  function jumpTo(year: number, month0: number) {
    let key = monthKey(year, month0);
    if (key < oldestKey) key = oldestKey; // clamp into the navigable stored range
    else if (key > newestKey) key = newestKey;
    const [yy, mm] = key.split("-").map(Number);
    setView({ year: yy, month0: mm - 1 });
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

  // Move the SINGLE GLOBAL as-of (J-71) one AVAILABLE snapshot date in `dir` (-1 = older/ArrowLeft,
  // +1 = newer/ArrowRight), bounded at the ends. The landing date is computed by the SHARED `resolveStep`
  // authority (J-79) — the SAME one the top-bar ◀ ▶ buttons and opt-in ← → keys use — so stepping is
  // identical everywhere (snapshot-only, never an arbitrary ±1 calendar day; bounded; newest→Latest/null).
  // It drives the EXISTING `onSelect`→`setAsOf` (no second date state), keeps the popover OPEN (no onClose),
  // and slides the local month-view cursor to follow the landing date.
  function stepAsOf(dir: -1 | 1) {
    const { changed, next } = resolveStep(dates, asOf, dir);
    if (!changed) return; // bounded: no-op at the oldest/newest
    onSelect(next);
    // Slide the viewed month (the only local state — a UI cursor, NOT an as-of value) to the landing month.
    // A null landing (Latest) follows the newest stored date so the grid shows the latest month.
    const landing = next ?? newest;
    if (landing) {
      const dt = parseIsoUTC(landing);
      setView({ year: dt.getUTCFullYear(), month0: dt.getUTCMonth() });
    }
  }

  // Keyboard: Escape closes; ArrowLeft/Right scrub the global as-of one available snapshot date (J-71),
  // staying open so the user can keep scrubbing live. Handled here on the dialog's onKeyDown (the dialog
  // is focused on open via data-autofocus) — NO global window/document listener (J-18 invariant).
  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      onClose();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      stepAsOf(-1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      stepAsOf(1);
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

      {/* J-79 — Year + Month quick-jump dropdowns: navigate the viewed month directly instead of clicking
          the chevrons month-by-month. They move the viewed-month cursor only (a presentation aid). */}
      <div className="mb-2 grid grid-cols-2 gap-2">
        <select
          aria-label="Jump to year"
          data-testid="asof-cal-year"
          value={view.year}
          onChange={(e) => jumpTo(Number(e.target.value), view.month0)}
          className={cn(
            "h-7 rounded-md border border-border bg-surface-2 px-2 text-xs text-text",
            "transition-colors hover:border-border-strong",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          )}
        >
          {yearOptions.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          aria-label="Jump to month"
          data-testid="asof-cal-month-select"
          value={view.month0}
          onChange={(e) => jumpTo(view.year, Number(e.target.value))}
          className={cn(
            "h-7 rounded-md border border-border bg-surface-2 px-2 text-xs text-text",
            "transition-colors hover:border-border-strong",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          )}
        >
          {MONTH_NAMES.map((name, i) => (
            <option key={name} value={i}>
              {name}
            </option>
          ))}
        </select>
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
