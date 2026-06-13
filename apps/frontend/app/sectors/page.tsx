"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ChevronDown, ChevronRight, Grid2x2 } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
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
  const { asOf } = useAsOf();
  // J-58 (mirrors J-57 Themes): the one shared helper builds every member-ticker href carrying the
  // global as-of date while historical (clean at latest) — used by the dated new-tab member links.
  const asofHref = useAsOfHref();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchSectors(asOf ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

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
            as of {formatIsoDate(state.data.asof_date)}
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
                  asofHref={asofHref}
                />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

/** J-58 (mirrors J-57 Themes) — the member preview limit: the first N members render inline, the
 *  remaining N collapse behind the expandable `+n` control (a re-display of the already-served member
 *  list — nothing refetched). Same constant convention as /themes for a consistent preview length. */
const MEMBER_PREVIEW_LIMIT = 6;

function SectorRows({
  row,
  open,
  onToggle,
  asofHref,
}: {
  row: SectorRow;
  open: boolean;
  onToggle: () => void;
  /** J-58: builds each member href carrying the global `?asof` while historical (clean at latest). */
  asofHref: (path: string) => string;
}) {
  // J-58: the member-list expand/collapse, LOCAL to this ETF row and INDEPENDENT of the row's own
  // expand (`open`). The `+n` control reveals EVERY remaining member in place; collapsing folds back to
  // the preview. A pure view transform over the already-served `row.members` — nothing refetched.
  const [membersExpanded, setMembersExpanded] = useState(false);
  const hasOverflow = row.members.length > MEMBER_PREVIEW_LIMIT;
  const shownMembers = membersExpanded ? row.members : row.members.slice(0, MEMBER_PREVIEW_LIMIT);
  const extra = row.members.length - MEMBER_PREVIEW_LIMIT;
  // Industry membership is config-curated reference data; label it honestly so the source is clear.
  const membersLabel = row.kind === "industry" ? "Members (config-defined)" : "Members";
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
        // The expanded panel is a SEPARATE, non-clickable <tr> — the description, member links, and
        // the `+n` control live here, NOT inside the clickable summary row, so they are not nested in
        // a role="button" element (iter-5 nested-interactive hazard). `stopPropagation` is added
        // defensively so a stray bubble can never toggle the summary row.
        <tr className="border-b border-border bg-bg">
          <td colSpan={8} className="px-4 py-3">
            <p className="mb-1 text-xs font-medium text-text">
              {row.ticker} — {row.name}
            </p>
            {/* J-58: the config description line (only when present — a sector ETF or a stored run
                predating the column has no description, and the row still renders honestly). */}
            {row.description ? (
              <p className="mb-3 max-w-2xl text-xs text-text-muted">{row.description}</p>
            ) : null}

            {/* J-58: the expandable universe-member list (sector members from stock_sectors, industry
                members from stock_industries). Zero members → explicit honest empty state. */}
            {row.members.length > 0 ? (
              <div className="mb-3 flex flex-wrap items-center gap-1.5">
                <span className="mr-1 text-xs uppercase tracking-wide text-text-faint">{membersLabel}</span>
                {shownMembers.map((ticker) => (
                  // J-58: every member ticker is a dated link OPENING IN A NEW TAB — the href carries
                  // the global `?asof` while historical (J-50), clean at latest; `rel="noopener
                  // noreferrer"` for new-tab safety. `stopPropagation` keeps a member click from
                  // toggling the summary row.
                  <Link
                    key={ticker}
                    href={asofHref(`/stocks/${ticker}`)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    data-testid="sector-member-link"
                    className="num rounded-sm border border-border bg-surface px-2 py-0.5 text-xs font-medium text-accent transition-colors hover:border-accent hover:underline focus-visible:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
                  >
                    {ticker}
                  </Link>
                ))}
                {hasOverflow ? (
                  // The `+n` expand/collapse control — a real <button> (keyboard + click accessible)
                  // living in the non-clickable panel row. It reveals EVERY remaining member in place /
                  // folds back; `stopPropagation` guards the summary row.
                  <button
                    type="button"
                    aria-expanded={membersExpanded}
                    onClick={(e) => {
                      e.stopPropagation();
                      setMembersExpanded((v) => !v);
                    }}
                    data-testid="sector-members-toggle"
                    className="num rounded-sm border border-dashed border-border px-2 py-0.5 text-xs text-text-faint transition-colors hover:border-accent hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
                  >
                    {membersExpanded ? "Show fewer" : `+${extra}`}
                  </button>
                ) : null}
              </div>
            ) : (
              // J-58: explicit honest empty state — NEVER fabricated members.
              <p data-testid="sector-members-empty" className="mb-3 text-xs italic text-text-faint">
                No universe members are mapped to this ETF
                {row.kind === "industry" ? " (config-defined)" : ""}.
              </p>
            )}

            <p className="mb-2 text-xs text-text-muted">
              Sector Score {row.score.toFixed(2)} (bucket {row.bucket})
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
