"use client";

import { Clock, History } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";

/**
 * Global top-bar as-of date switcher (iter-8, J-13). Picks any past trading day from the canonical
 * immutable run list to time-travel the whole dashboard, and renders a clear "viewing as-of D
 * (historical)" indicator (the `--warn` amber token) whenever the selected date ≠ latest. The
 * latest/current state is visually quiet. Additive top-bar control — no new page or sidebar change.
 */
export function AsOfSwitcher() {
  const { asOf, setAsOf, latest, dates, isHistorical, ready } = useAsOf();

  // Historical options = every run date except the latest (the latest is the default "Latest" option).
  const historical = dates.filter((date) => date !== latest);

  return (
    <div className="flex items-center gap-2">
      {isHistorical ? (
        <Badge variant="warn" className="num gap-1.5" aria-live="polite" data-testid="asof-indicator">
          <History className="h-3.5 w-3.5" aria-hidden />
          Viewing as-of {asOf} (historical)
        </Badge>
      ) : (
        <Badge variant="default" className="gap-1.5" data-testid="asof-indicator">
          <Clock className="h-3.5 w-3.5" aria-hidden />
          Latest
        </Badge>
      )}
      <label className="flex items-center gap-1.5 text-xs text-text-muted">
        <span className="sr-only">View as-of date</span>
        <Select
          aria-label="View as-of date"
          className="num w-44"
          value={asOf ?? ""}
          disabled={!ready || dates.length === 0}
          onChange={(event) => setAsOf(event.target.value || null)}
        >
          <option value="">Latest{latest ? ` · ${latest}` : ""}</option>
          {historical.map((date) => (
            <option key={date} value={date}>
              {date}
            </option>
          ))}
        </Select>
      </label>
    </div>
  );
}
