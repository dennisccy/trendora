import * as React from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * A palette-themed wrapper around the native <select> — used for the dense leaderboard filters.
 * (The project has no Radix Select dependency; a styled native control keeps filters dependency-free
 * and accessible, with the design-system tokens, hover/focus states, and a consistent chevron.)
 */
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <div className="relative inline-flex items-center">
      <select
        ref={ref}
        className={cn(
          "h-9 w-full appearance-none rounded-md border border-border bg-surface-2 pl-3 pr-8 text-sm text-text",
          "transition-colors hover:border-border-strong",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2 h-4 w-4 text-text-faint" aria-hidden />
    </div>
  ),
);
Select.displayName = "Select";
