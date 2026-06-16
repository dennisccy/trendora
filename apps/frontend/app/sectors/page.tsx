"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowDown, ArrowUp, ArrowUpDown, ChevronDown, ChevronRight, Grid2x2 } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
// J-81: the SHARED forward-return formatter/colour helper (the same one /stocks J-75 + the evidence
// tables use) — aliased so it does not collide with this page's local no-sign `fmtPct` (dist-from-high).
import { fmtPct as fmtFwdPct, returnClass } from "@/components/forward-return";
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

// J-81 / J-48 — the sortable column keys: the stored rank (default), Sector Score, and the dynamic
// forward-return columns `fwd_<horizon>`. A pure VIEW transform — sorting only re-orders the served rows;
// it recomputes/refetches nothing and never changes a displayed value.
type BaseSortKey = "rank" | "score";
type SortKey = BaseSortKey | `fwd_${number}`;
type SortDir = "asc" | "desc";

/** J-81 — a sector ETF's realized forward return at `horizon` from the served `forward_returns`
 *  (NA → null). Read verbatim; never recomputed. */
function fwdReturnAt(row: SectorRow, horizon: number): number | null {
  return row.forward_returns.find((fr) => fr.horizon === horizon)?.return ?? null;
}

const BASE_COMPARATORS: Record<BaseSortKey, (a: SectorRow, b: SectorRow) => number> = {
  rank: (a, b) => a.rank - b.rank,
  score: (a, b) => a.score - b.score,
};

/** Resolve a sort key to its comparator. A null (NA) forward return ALWAYS sorts LAST regardless of
 *  direction; the stable memo then tie-breaks by stored rank. Pure re-order of served values. */
function comparatorFor(key: SortKey, dir: SortDir): (a: SectorRow, b: SectorRow) => number {
  if (key.startsWith("fwd_")) {
    const horizon = Number(key.slice(4));
    const sign = dir === "asc" ? 1 : -1;
    return (a, b) => {
      const av = fwdReturnAt(a, horizon);
      const bv = fwdReturnAt(b, horizon);
      if (av === null && bv === null) return 0;
      if (av === null) return 1; // NA last regardless of direction
      if (bv === null) return -1;
      return (av - bv) * sign;
    };
  }
  const cmp = BASE_COMPARATORS[key as BaseSortKey];
  const sign = dir === "asc" ? 1 : -1;
  return (a, b) => cmp(a, b) * sign;
}

/** The default sort: the scanner's stored sector rank, ascending (`#`). */
const DEFAULT_SORT: { key: SortKey; dir: SortDir } = { key: "rank", dir: "asc" };

/** J-81/J-48 — a sortable column header (mirrors the /stocks + /themes SortHeader pattern). */
function SortHeader({
  col,
  label,
  activeKey,
  dir,
  onSort,
}: {
  col: SortKey;
  label: string;
  activeKey: SortKey;
  dir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const active = activeKey === col;
  const ariaSort: "ascending" | "descending" | "none" = active
    ? dir === "asc"
      ? "ascending"
      : "descending"
    : "none";
  const isFwd = col.startsWith("fwd_");
  return (
    <th className={cn("px-3 py-2 font-medium", isFwd && "text-right")} aria-sort={ariaSort}>
      <button
        type="button"
        onClick={() => onSort(col)}
        aria-label={`Sort by ${label}${active ? (dir === "asc" ? ", ascending" : ", descending") : ""}`}
        className={cn(
          "group inline-flex items-center gap-1 rounded-sm uppercase tracking-wide transition-colors hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          isFwd && "justify-end",
        )}
      >
        <span className={cn(active && "text-text")}>{label}</span>
        {active ? (
          dir === "asc" ? (
            <ArrowUp className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
          ) : (
            <ArrowDown className="h-3 w-3 text-accent" aria-hidden data-testid="sort-indicator" />
          )
        ) : (
          <ArrowUpDown
            className="h-3 w-3 text-text-faint/40 opacity-0 transition-opacity group-hover:opacity-100"
            aria-hidden
          />
        )}
      </button>
    </th>
  );
}

/** J-81 — one colour-graded forward-return cell: the served realized return (NA → "NA" muted), read
 *  verbatim. Positive green / negative red via the shared palette helper (same as the evidence tables). */
function ForwardReturnCell({ value }: { value: number | null }) {
  if (value === null || value === undefined) {
    return (
      <span className="num text-text-muted" title="No realized forward return at this horizon yet (NA)">
        NA
      </span>
    );
  }
  return <span className={cn("num font-semibold", returnClass(value))}>{fmtFwdPct(value)}</span>;
}

export default function SectorsPage() {
  const { asOf } = useAsOf();
  // J-58 (mirrors J-57 Themes): the one shared helper builds every member-ticker href carrying the
  // global as-of date while historical (clean at latest) — used by the dated new-tab member links.
  const asofHref = useAsOfHref();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<SortKey>(DEFAULT_SORT.key);
  const [sortDir, setSortDir] = useState<SortDir>(DEFAULT_SORT.dir);

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

  // J-81 — the forward-return column horizons, derived from the SERVED rows (config-driven; no hardcoded
  // [1,5,10,20,60] in the UI). Read from the first row's `forward_returns` order.
  const rows = state.kind === "ok" ? state.data.rows : [];
  const fwdHorizons = useMemo(
    () => (rows.length > 0 ? rows[0].forward_returns.map((fr) => fr.horizon) : []),
    [rows],
  );

  // J-81/J-48 — the sorted view: a STABLE sort (stored rank tie-break) over the served rows. Recomputes
  // no value; an unknown sort key harmlessly falls back to the stored rank order.
  const sorted = useMemo(() => {
    const cmp = comparatorFor(sortKey, sortDir);
    return rows
      .map((row, i) => ({ row, i }))
      .sort((a, b) => {
        const c = cmp(a.row, b.row);
        return c !== 0 ? c : a.row.rank - b.row.rank || a.i - b.i;
      })
      .map((x) => x.row);
  }, [rows, sortKey, sortDir]);

  const onSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      // forward-return columns lead descending (best return first); other columns ascend.
      setSortDir(key.startsWith("fwd_") ? "desc" : "asc");
    }
  };

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
                <SortHeader col="rank" label="#" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-3 py-2 font-medium">Ticker</th>
                <th className="px-3 py-2 font-medium">Kind</th>
                <SortHeader col="score" label="Sector Score" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-3 py-2 text-right font-medium">RS vs SPY</th>
                <th className="px-3 py-2 text-right font-medium">Dist. 52w high</th>
                {/* J-81 — five realized forward-return columns (1/5/10/20/60-day from config horizons),
                    each client-side sortable (view transform, NA-last). The horizons are server-driven
                    (from the row payload), so no hardcoded horizon list lives in the UI. The value is the
                    ETF's OWN forward return Backtest's Top Sectors shows for the same date+horizon. */}
                {fwdHorizons.map((h) => (
                  <SortHeader
                    key={`fwd_${h}`}
                    col={`fwd_${h}` as SortKey}
                    label={`${h}d`}
                    activeKey={sortKey}
                    dir={sortDir}
                    onSort={onSort}
                  />
                ))}
                <th className="px-3 py-2 font-medium">Trend</th>
                <th className="px-3 py-2" aria-label="expand" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <SectorRows
                  key={row.ticker}
                  row={row}
                  open={expanded.has(row.ticker)}
                  onToggle={() => toggle(row.ticker)}
                  asofHref={asofHref}
                  fwdHorizons={fwdHorizons}
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
  fwdHorizons,
}: {
  row: SectorRow;
  open: boolean;
  onToggle: () => void;
  /** J-58: builds each member href carrying the global `?asof` while historical (clean at latest). */
  asofHref: (path: string) => string;
  /** J-81 — the server-driven forward-return column horizons (config order), rendered as cells. */
  fwdHorizons: number[];
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
  // the expanded panel spans every column: rank + ticker + kind + score + RS + dist + N fwd + trend + chevron
  const colSpan = 6 + fwdHorizons.length + 2;
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
        {/* J-81 — five realized forward-return cells (config horizons, colour-graded, NA where no stored
            row — industry ETFs without a bar render NA honestly). Read verbatim — never recomputed. */}
        {fwdHorizons.map((h) => (
          <td key={`fwd_${h}`} className="px-3 py-2 text-right" data-testid={`sector-fwd-${h}`}>
            <ForwardReturnCell value={row.forward_returns.find((fr) => fr.horizon === h)?.return ?? null} />
          </td>
        ))}
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
          <td colSpan={colSpan} className="px-4 py-3">
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
