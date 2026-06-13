"use client";

import { useEffect, useRef, useState } from "react";
import { CalendarDays, ChevronDown, Clock, History } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { AsOfCalendar } from "@/components/asof-calendar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";

/**
 * Global top-bar as-of date switcher (iter-8, J-13; J-62 calendar popover). Picks any past trading day
 * from the canonical immutable run list to time-travel the whole dashboard, and renders a clear
 * "viewing as-of D (historical)" indicator (the `--warn` amber token) whenever the selected date ≠
 * latest. The latest/current state is visually quiet. Additive top-bar control — no new page or sidebar.
 *
 * J-62: the date is chosen from a CALENDAR POPOVER (a month grid that marks only the selectable snapshot
 * dates) instead of a flat dropdown. The popover is a pure RENDERER of the one global control — selecting
 * a day calls the EXISTING `setAsOf` (unchanged), so the historical badge, the `?asof` URL serialization
 * (J-43), and the href stamping (J-50) all stay byte-unchanged. There is NO second date state: the
 * provider remains the single owner of the as-of value and its URL serialization. With no available
 * dates the control is disabled.
 */
export function AsOfSwitcher() {
  const { asOf, setAsOf, latest, dates, isHistorical, ready } = useAsOf();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const disabled = !ready || dates.length === 0;

  // Close the popover on an outside click. (Escape is handled inside the calendar; a selection closes it.)
  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  return (
    <div className="flex items-center gap-2" ref={rootRef}>
      {isHistorical ? (
        <Badge variant="warn" className="num gap-1.5" aria-live="polite" data-testid="asof-indicator">
          <History className="h-3.5 w-3.5" aria-hidden />
          Viewing as-of {formatIsoDate(asOf)} (historical)
        </Badge>
      ) : (
        <Badge variant="default" className="gap-1.5" data-testid="asof-indicator">
          <Clock className="h-3.5 w-3.5" aria-hidden />
          Latest
        </Badge>
      )}

      <div className="relative">
        <span className="sr-only" id="asof-switcher-label">
          View as-of date
        </span>
        <button
          type="button"
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-labelledby="asof-switcher-label"
          aria-label="View as-of date"
          data-testid="asof-trigger"
          disabled={disabled}
          onClick={() => setOpen((v) => !v)}
          className={cn(
            "inline-flex h-9 w-44 items-center justify-between gap-1.5 rounded-md border border-border bg-surface-2 px-3 text-sm text-text",
            "transition-colors hover:border-border-strong",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          <span className="flex items-center gap-1.5">
            <CalendarDays className="h-3.5 w-3.5 text-text-faint" aria-hidden />
            <span className="num truncate">
              {isHistorical && asOf ? formatIsoDate(asOf) : "Latest"}
            </span>
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-text-faint" aria-hidden />
        </button>

        {open && !disabled ? (
          <div className="absolute right-0 z-50 mt-1">
            <AsOfCalendar
              dates={dates}
              latest={latest}
              asOf={asOf}
              onSelect={setAsOf}
              onClose={() => setOpen(false)}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
