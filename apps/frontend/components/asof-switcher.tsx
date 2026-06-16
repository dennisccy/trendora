"use client";

import { useEffect, useRef, useState } from "react";
import { CalendarDays, ChevronDown, ChevronLeft, ChevronRight, Clock, History } from "lucide-react";

import { useAsOf, useAsOfStep } from "@/components/asof-provider";
import { AsOfCalendar } from "@/components/asof-calendar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatIsoDate } from "@/lib/dates";
import { isFieldEditingTarget } from "@/lib/asof-step";
import { usePersistedToggle } from "@/lib/use-persisted-toggle";

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
 *
 * J-79: the date can also be STEPPED one available snapshot at a time with the popover CLOSED, two ways,
 * both driving the SAME single global `setAsOf` via `useAsOfStep` (so NO second/page-local date state and
 * the `?asof` serialization stays in sync):
 *   • always-visible ◀ / ▶ buttons beside the control, bounded (disabled at the oldest / newest);
 *   • a PERSISTED, DEFAULT-OFF "← → steps date" checkbox that, when on, enables a FIELD-GUARDED global key
 *     handler — ← / → step the date exactly like the buttons. The handler never fires while focus is in an
 *     input / textarea / select / contenteditable (the caret moves instead — goal.md J-79 step 5) and is
 *     installed only while the checkbox is on (it never hijacks scrolling when off). This SUPERSEDES the
 *     J-71 "no global window listener" wording ONLY behind this opt-in toggle; the calendar's panel-open
 *     onKeyDown (J-71) is unchanged.
 */
export function AsOfSwitcher() {
  const { asOf, setAsOf, latest, dates, isHistorical, ready } = useAsOf();
  const { stepPrev, stepNext, canPrev, canNext } = useAsOfStep();
  const [open, setOpen] = useState(false);
  // J-79 — the opt-in, default-off, persisted arrow-key preference (same localStorage pattern as the
  // index-chart / regime-band toggles). Default OFF so a fresh browser never globally intercepts arrows.
  const [arrowSteps, setArrowSteps] = usePersistedToggle("asof-arrow-steps", false);
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

  // J-79 — the field-guarded global key handler. Installed ONLY while the opt-in checkbox is on AND the
  // control is usable (so it never hijacks arrows when off, and never installs before the run list loads).
  // It is a no-op when the calendar popover is open (the popover's own onKeyDown owns arrows then — J-71),
  // and it is ignored while focus is in a text-entry field (← / → move the caret instead — J-79 step 5).
  // Stepping drives the SAME `useAsOfStep` the buttons use → the one global state, no second date state.
  useEffect(() => {
    if (!arrowSteps || disabled) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      if (open) return; // the open popover owns arrow scrubbing (J-71)
      if (isFieldEditingTarget(e.target as { tagName?: string; isContentEditable?: boolean } | null)) {
        return; // typing in a field — let the caret move, never change the date (J-79 step 5)
      }
      e.preventDefault(); // we are handling it: don't also scroll the page
      if (e.key === "ArrowLeft") stepPrev();
      else stepNext();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [arrowSteps, disabled, open, stepPrev, stepNext]);

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

      {/* J-79 — ◀ prev / ▶ next stepper buttons. Always visible beside the control; bounded (disabled at
          the oldest going older / the newest going newer); step ONE available snapshot via the single
          global state — the popover stays closed so the view is never covered. */}
      <button
        type="button"
        aria-label="Previous available date"
        data-testid="asof-step-prev"
        disabled={disabled || !canPrev}
        onClick={stepPrev}
        className={cn(
          "inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-surface-2 text-text-muted",
          "transition-colors hover:border-border-strong hover:text-text",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          "disabled:cursor-not-allowed disabled:opacity-40",
        )}
      >
        <ChevronLeft className="h-4 w-4" aria-hidden />
      </button>
      <button
        type="button"
        aria-label="Next available date"
        data-testid="asof-step-next"
        disabled={disabled || !canNext}
        onClick={stepNext}
        className={cn(
          "inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-surface-2 text-text-muted",
          "transition-colors hover:border-border-strong hover:text-text",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          "disabled:cursor-not-allowed disabled:opacity-40",
        )}
      >
        <ChevronRight className="h-4 w-4" aria-hidden />
      </button>

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

      {/* J-79 — the opt-in, persisted, default-off "← → steps date" checkbox. When off (the default) the
          global key handler above is not installed, so arrows behave normally everywhere. */}
      <label
        className="flex cursor-pointer select-none items-center gap-1.5 text-xs text-text-muted"
        title="When on, the ← / → arrow keys step the as-of date (ignored while typing in a field)"
      >
        <input
          type="checkbox"
          checked={arrowSteps}
          onChange={(e) => setArrowSteps(e.target.checked)}
          disabled={disabled}
          data-testid="asof-arrow-toggle"
          className={cn(
            "h-3.5 w-3.5 rounded border-border bg-surface-2 text-accent accent-accent",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        />
        ← → steps date
      </label>
    </div>
  );
}
