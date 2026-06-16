"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowDown, ArrowUp, ArrowUpDown, ChevronDown, ChevronRight, Layers } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
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

// J-81 / J-48 — the sortable column keys: the stored rank (default), Theme Score, and the dynamic
// forward-return columns `fwd_<horizon>`. A pure VIEW transform — sorting only re-orders the served
// rows; it recomputes/refetches nothing and never changes a displayed value.
type BaseSortKey = "rank" | "score";
type SortKey = BaseSortKey | `fwd_${number}`;
type SortDir = "asc" | "desc";

/** J-81 — a theme's realized forward return at `horizon` from the served `forward_returns` (NA → null).
 *  Read verbatim; never recomputed. */
function fwdReturnAt(row: ThemeRow, horizon: number): number | null {
  return row.forward_returns.find((fr) => fr.horizon === horizon)?.return ?? null;
}

const BASE_COMPARATORS: Record<BaseSortKey, (a: ThemeRow, b: ThemeRow) => number> = {
  rank: (a, b) => a.rank - b.rank,
  score: (a, b) => a.score - b.score,
};

/** Resolve a sort key to its comparator. A null (NA) forward return ALWAYS sorts LAST regardless of
 *  direction (NA never poses as a top/bottom value); the stable memo then tie-breaks by stored rank.
 *  Pure re-order of served values (J-81/J-48 view-transform contract). */
function comparatorFor(key: SortKey, dir: SortDir): (a: ThemeRow, b: ThemeRow) => number {
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

/** The default sort: the scanner's stored theme rank, ascending (`#`). */
const DEFAULT_SORT: { key: SortKey; dir: SortDir } = { key: "rank", dir: "asc" };

export default function ThemesPage() {
  const { asOf } = useAsOf();
  // J-57: the one shared helper builds every member-ticker href carrying the global as-of date while
  // historical (clean at latest) — used by the dated new-tab member links in the expanded panel below.
  const asofHref = useAsOfHref();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<SortKey>(DEFAULT_SORT.key);
  const [sortDir, setSortDir] = useState<SortDir>(DEFAULT_SORT.dir);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchThemes(asOf ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

  const toggle = (slug: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
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
        title="Themes"
        subtitle="Theme Leaderboard — ranked by a price-confirmed Theme Score (basket RS-vs-SPY · member breadth · MA participation)"
      />

      {state.kind === "ok" && state.data.rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
          <Badge variant="default" className="num">
            as of {formatIsoDate(state.data.asof_date)}
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
                <SortHeader col="rank" label="#" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-3 py-2 font-medium">Theme</th>
                <SortHeader col="score" label="Theme Score" activeKey={sortKey} dir={sortDir} onSort={onSort} />
                <th className="px-3 py-2 text-right font-medium">1m</th>
                <th className="px-3 py-2 text-right font-medium">3m</th>
                <th className="px-3 py-2 text-right font-medium">Breadth</th>
                {/* J-81 — five realized forward-return columns (1/5/10/20/60-day from config horizons),
                    each client-side sortable (view transform, NA-last). The horizons are server-driven
                    (from the row payload), so no hardcoded horizon list lives in the UI. The value is the
                    equal-weight member-basket return Backtest's Top Themes shows for the same date+horizon. */}
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
                <ThemeRows
                  key={row.slug}
                  row={row}
                  open={expanded.has(row.slug)}
                  onToggle={() => toggle(row.slug)}
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

/** J-81/J-48 — a sortable column header (mirrors the /stocks SortHeader pattern). The sort control is a
 *  real <button> (keyboard + click accessible); the active column shows the direction arrow. */
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
  // forward-return columns are right-aligned numeric (match the 1m/3m/Breadth cells); base columns left.
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
  return <span className={cn("num font-semibold", returnClass(value))}>{fmtPct(value)}</span>;
}

/** J-57 — the member preview limit: the first N members render inline, the remaining N collapse behind
 *  the expandable `+n` control (a re-display of the already-served member list — nothing refetched). */
const MEMBER_PREVIEW_LIMIT = 6;

function ThemeRows({
  row,
  open,
  onToggle,
  asofHref,
  fwdHorizons,
}: {
  row: ThemeRow;
  open: boolean;
  onToggle: () => void;
  /** J-57: builds each member href carrying the global `?asof` while historical (clean at latest). */
  asofHref: (path: string) => string;
  /** J-81 — the server-driven forward-return column horizons (config order), rendered as cells. */
  fwdHorizons: number[];
}) {
  // J-57: the member-list expand/collapse, LOCAL to this theme row and INDEPENDENT of the row's own
  // expand (`open`). The `+n` control reveals EVERY remaining member in place; collapsing folds back to
  // the preview. A pure view transform over the already-served `row.members` — nothing refetched.
  const [membersExpanded, setMembersExpanded] = useState(false);
  const hasOverflow = row.members.length > MEMBER_PREVIEW_LIMIT;
  const shownMembers = membersExpanded ? row.members : row.members.slice(0, MEMBER_PREVIEW_LIMIT);
  const extra = row.members.length - MEMBER_PREVIEW_LIMIT;
  // the expanded panel spans every column: rank + theme + score + 1m + 3m + breadth + N fwd + trend + chevron
  const colSpan = 7 + fwdHorizons.length + 1;
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
        {/* J-81 — five realized forward-return cells (config horizons, colour-graded, NA where no stored
            member return). Read verbatim from the served row — never recomputed. */}
        {fwdHorizons.map((h) => (
          <td key={`fwd_${h}`} className="px-3 py-2 text-right" data-testid={`theme-fwd-${h}`}>
            <ForwardReturnCell value={row.forward_returns.find((fr) => fr.horizon === h)?.return ?? null} />
          </td>
        ))}
        <td className="px-3 py-2 text-text-muted">{row.trend_label}</td>
        <td className="px-3 py-2 text-text-faint">
          {open ? <ChevronDown className="h-4 w-4" aria-hidden /> : <ChevronRight className="h-4 w-4" aria-hidden />}
        </td>
      </tr>
      {open ? (
        // The expanded panel is a SEPARATE, non-clickable <tr> — the member links and the `+n` control
        // live here, NOT inside the clickable summary row, so they are not nested in a role="button"
        // element (iter-5 lesson). `stopPropagation` is added defensively so a stray bubble can never
        // toggle the summary row even if the markup is later reorganized.
        <tr className="border-b border-border bg-bg">
          <td colSpan={colSpan} className="px-4 py-3">
            <div className="mb-3 flex flex-wrap items-center gap-1.5">
              <span className="mr-1 text-xs uppercase tracking-wide text-text-faint">Members</span>
              {shownMembers.map((ticker) => (
                // J-57: every member ticker is a dated link OPENING IN A NEW TAB — the href carries the
                // global `?asof` while historical (J-50), clean at latest; `rel="noopener noreferrer"` for
                // new-tab safety. `stopPropagation` keeps a member click from toggling the summary row.
                <Link
                  key={ticker}
                  href={asofHref(`/stocks/${ticker}`)}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  data-testid="theme-member-link"
                  className="num rounded-sm border border-border bg-surface px-2 py-0.5 text-xs font-medium text-accent transition-colors hover:border-accent hover:underline focus-visible:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
                >
                  {ticker}
                </Link>
              ))}
              {hasOverflow ? (
                // The `+n` expand/collapse control — a real <button> (keyboard + click accessible) living
                // in the non-clickable panel row, so it is NOT nested in a clickable element. It reveals
                // EVERY remaining member in place / folds back; `stopPropagation` guards the summary row.
                <button
                  type="button"
                  aria-expanded={membersExpanded}
                  onClick={(e) => {
                    e.stopPropagation();
                    setMembersExpanded((v) => !v);
                  }}
                  data-testid="theme-members-toggle"
                  className="num rounded-sm border border-dashed border-border px-2 py-0.5 text-xs text-text-faint transition-colors hover:border-accent hover:text-text focus-visible:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
                >
                  {membersExpanded ? "Show fewer" : `+${extra}`}
                </button>
              ) : null}
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
