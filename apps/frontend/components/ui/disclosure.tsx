"use client";

import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

/** A lightweight inline disclosure (native `<details>`) — keeps a figure's named breakdown REACHABLE
 *  (one click) without crowding the surrounding summary. Pure presentation, no business logic.
 *
 *  Extracted from the Dashboard page (J-98) so the goal-market-compass iter-2 "Show cited facts" and
 *  "suppressed moves" disclosures reuse the SAME component rather than a third hand-copied `<details>`
 *  block. */
export function Disclosure({ summary, children }: { summary: string; children: React.ReactNode }) {
  return (
    <details className="group rounded border border-border bg-surface-2/40">
      <summary
        className={cn(
          "flex cursor-pointer list-none items-center justify-between gap-2 px-2.5 py-1.5 text-xs text-text-muted",
          "transition-colors hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        {summary}
        <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <div className="border-t border-border px-2.5 pb-2.5">{children}</div>
    </details>
  );
}
