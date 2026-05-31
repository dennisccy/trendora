"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Info } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * A hand-rolled, dependency-free, accessible info affordance (iter-12). Its content is revealed on
 * HOVER, keyboard-FOCUS, AND tap/CLICK — so "hover/tap a badge to read the definition" works on
 * desktop and touch, and is deterministically assertable by browser-QA (a click pins the panel open
 * until an outside click or Escape). Styled with palette tokens on a Card-like surface.
 *
 * Open state = transient (hover/focus) OR pinned (click). The panel content is only mounted while
 * open, so the revealed text is unambiguously present in the DOM after the interaction.
 */
export function InfoTooltip({
  label,
  content,
  className,
}: {
  label: string; // accessible name for the trigger, e.g. "Definition of Actionable"
  content: ReactNode; // the definition (rendered inside the panel)
  className?: string;
}) {
  const [transient, setTransient] = useState(false); // hover / keyboard focus
  const [pinned, setPinned] = useState(false); // click / tap (sticky)
  const open = transient || pinned;
  const panelId = useId();
  const wrapRef = useRef<HTMLSpanElement>(null);

  // Dismiss a pinned panel on an outside click or Escape (touch-friendly).
  useEffect(() => {
    if (!pinned) return;
    function onPointerDown(event: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(event.target as Node)) {
        setPinned(false);
        setTransient(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setPinned(false);
        setTransient(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [pinned]);

  return (
    <span
      ref={wrapRef}
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setTransient(true)}
      onMouseLeave={() => setTransient(false)}
    >
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-describedby={open ? panelId : undefined}
        onClick={() => setPinned((value) => !value)}
        onFocus={() => setTransient(true)}
        onBlur={() => setTransient(false)}
        className={cn(
          "inline-flex h-4 w-4 items-center justify-center rounded-full text-text-faint",
          "transition-colors hover:text-accent",
          "focus-visible:text-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        <Info className="h-3.5 w-3.5" aria-hidden />
      </button>
      {open ? (
        <span
          id={panelId}
          role="tooltip"
          className={cn(
            "absolute left-0 top-full z-30 mt-1 w-64 rounded-md border border-border bg-surface p-3",
            "text-left text-xs font-normal leading-relaxed text-text-muted shadow-lg",
          )}
        >
          {content}
        </span>
      ) : null}
    </span>
  );
}
