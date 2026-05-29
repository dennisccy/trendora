"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight, Layers } from "lucide-react";

import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { fetchThemes, type ThemeRow, type ThemesResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: ThemesResponse }
  | { kind: "error" };

function fmtSignedPct(value: number | null): string {
  if (value === null) return "NA";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export default function ThemesPage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    const controller = new AbortController();
    fetchThemes(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const toggle = (slug: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next;
    });

  return (
    <div className="space-y-4">
      <PageHeading
        title="Themes"
        subtitle="Theme Leaderboard — ranked by a price-confirmed Theme Score (basket RS-vs-SPY · member breadth · MA participation)"
      />

      {state.kind === "ok" && state.data.rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
          <Badge variant="default" className="num">
            as of {state.data.asof_date}
          </Badge>
          <Badge variant="warn">breadth is universe-relative</Badge>
          <span>Price-confirmed, not news-driven. Click a row for its component breakdown.</span>
        </div>
      ) : null}

      {state.kind === "loading" ? <ThemesSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Theme Leaderboard could not load from the API. No rankings are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && state.data.rows.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No ranked themes"
          description="The backend returned no theme rows for the current data date."
        />
      ) : null}

      {state.kind === "ok" && state.data.rows.length > 0 ? (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Theme</th>
                <th className="px-3 py-2 font-medium">Theme Score</th>
                <th className="px-3 py-2 text-right font-medium">1m</th>
                <th className="px-3 py-2 text-right font-medium">3m</th>
                <th className="px-3 py-2 text-right font-medium">Breadth</th>
                <th className="px-3 py-2 font-medium">Trend</th>
                <th className="px-3 py-2" aria-label="expand" />
              </tr>
            </thead>
            <tbody>
              {state.data.rows.map((row) => (
                <ThemeRows
                  key={row.slug}
                  row={row}
                  open={expanded.has(row.slug)}
                  onToggle={() => toggle(row.slug)}
                />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

function ThemeRows({ row, open, onToggle }: { row: ThemeRow; open: boolean; onToggle: () => void }) {
  const shownMembers = row.members.slice(0, 6);
  const extra = row.members.length - shownMembers.length;
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
        <td className="px-3 py-2 font-semibold text-text">{row.name}</td>
        <td className="px-3 py-2">
          <ScoreBadge bucket={row.bucket} score={row.score} />
        </td>
        <td className={cn("num px-3 py-2 text-right", row.return_1m === null ? "text-warn" : row.return_1m >= 0 ? "text-pos" : "text-neg")}>
          {fmtSignedPct(row.return_1m)}
        </td>
        <td className={cn("num px-3 py-2 text-right", row.return_3m === null ? "text-warn" : row.return_3m >= 0 ? "text-pos" : "text-neg")}>
          {fmtSignedPct(row.return_3m)}
        </td>
        <td className={cn("num px-3 py-2 text-right", row.breadth_pct === null && "text-warn")}>
          {row.breadth_pct === null ? "NA" : `${row.breadth_pct.toFixed(0)}%`}
        </td>
        <td className="px-3 py-2 text-text-muted">{row.trend_label}</td>
        <td className="px-3 py-2 text-text-faint">
          {open ? <ChevronDown className="h-4 w-4" aria-hidden /> : <ChevronRight className="h-4 w-4" aria-hidden />}
        </td>
      </tr>
      {open ? (
        <tr className="border-b border-border bg-bg">
          <td colSpan={8} className="px-4 py-3">
            <div className="mb-3 flex flex-wrap items-center gap-1.5">
              <span className="mr-1 text-xs uppercase tracking-wide text-text-faint">Members</span>
              {shownMembers.map((ticker) => (
                <Badge key={ticker} variant="default" className="num">
                  {ticker}
                </Badge>
              ))}
              {extra > 0 ? <span className="num text-xs text-text-faint">+{extra}</span> : null}
            </div>
            <p className="mb-2 text-xs text-text-muted">
              {row.name} · Theme Score {row.score.toFixed(2)} (bucket {row.bucket}) · breadth{" "}
              {row.breadth_pct === null ? "NA" : `${row.breadth_pct.toFixed(0)}%`} ({row.breadth_label})
            </p>
            <ComponentBreakdown components={row.components} className="max-w-xl" />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function ThemesSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
