"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight, Grid2x2 } from "lucide-react";

import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { fetchSectors, type SectorRow, type SectorsResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: SectorsResponse }
  | { kind: "error" };

function fmtSignedPct(value: number | null): string {
  if (value === null) return "NA";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function fmtPct(value: number | null): string {
  if (value === null) return "NA";
  return `${value.toFixed(2)}%`;
}

export default function SectorsPage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    const controller = new AbortController();
    fetchSectors(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const toggle = (ticker: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(ticker) ? next.delete(ticker) : next.add(ticker);
      return next;
    });

  return (
    <div className="space-y-4">
      <PageHeading
        title="Sectors"
        subtitle="Sector / industry Leaderboard — ranked by Sector Score (RS-vs-SPY · MA stack · distance-from-52w-high · volume trend)"
      />

      {state.kind === "ok" && state.data.rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
          <Badge variant="default" className="num">
            as of {state.data.asof_date}
          </Badge>
          <Badge variant="accent">RS benchmark: {state.data.benchmark} (excluded)</Badge>
          <span>Leadership is relative across sector &amp; industry ETFs. Click a row for its component breakdown.</span>
        </div>
      ) : null}

      {state.kind === "loading" ? <SectorsSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Sector Leaderboard could not load from the API. No rankings are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && state.data.rows.length === 0 ? (
        <EmptyState
          icon={Grid2x2}
          title="No ranked sectors"
          description="The backend returned no sector/industry rows for the current data date."
        />
      ) : null}

      {state.kind === "ok" && state.data.rows.length > 0 ? (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Ticker</th>
                <th className="px-3 py-2 font-medium">Kind</th>
                <th className="px-3 py-2 font-medium">Sector Score</th>
                <th className="px-3 py-2 text-right font-medium">RS vs SPY</th>
                <th className="px-3 py-2 text-right font-medium">Dist. 52w high</th>
                <th className="px-3 py-2 font-medium">Trend</th>
                <th className="px-3 py-2" aria-label="expand" />
              </tr>
            </thead>
            <tbody>
              {state.data.rows.map((row) => (
                <SectorRows
                  key={row.ticker}
                  row={row}
                  open={expanded.has(row.ticker)}
                  onToggle={() => toggle(row.ticker)}
                />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

function SectorRows({
  row,
  open,
  onToggle,
}: {
  row: SectorRow;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr
        role="button"
        tabIndex={0}
        aria-expanded={open}
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
        className={cn(
          "cursor-pointer border-b border-border transition-colors",
          "hover:bg-surface-2 focus-visible:bg-surface-2 focus-visible:outline-none active:bg-border",
          open && "bg-surface-2",
        )}
      >
        <td className="num px-3 py-2 text-text-faint">{row.rank}</td>
        <td className="num px-3 py-2 font-semibold text-text">{row.ticker}</td>
        <td className="px-3 py-2">
          <Badge variant="default" className="capitalize">{row.kind}</Badge>
        </td>
        <td className="px-3 py-2">
          <ScoreBadge bucket={row.bucket} score={row.score} />
        </td>
        <td
          className={cn(
            "num px-3 py-2 text-right",
            row.rs_vs_spy === null ? "text-warn" : row.rs_vs_spy >= 0 ? "text-pos" : "text-neg",
          )}
        >
          {fmtSignedPct(row.rs_vs_spy)}
        </td>
        <td className={cn("num px-3 py-2 text-right", row.dist_from_52w_high_pct === null && "text-warn")}>
          {fmtPct(row.dist_from_52w_high_pct)}
        </td>
        <td className="px-3 py-2 text-text-muted">{row.trend_label}</td>
        <td className="px-3 py-2 text-text-faint">
          {open ? <ChevronDown className="h-4 w-4" aria-hidden /> : <ChevronRight className="h-4 w-4" aria-hidden />}
        </td>
      </tr>
      {open ? (
        <tr className="border-b border-border bg-bg">
          <td colSpan={8} className="px-4 py-3">
            <p className="mb-2 text-xs text-text-muted">
              {row.ticker} — {row.name} · Sector Score {row.score.toFixed(2)} (bucket {row.bucket})
            </p>
            <ComponentBreakdown components={row.components} className="max-w-xl" />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function SectorsSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
