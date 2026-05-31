"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, TrendingUp } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { fetchStocks, type StockRow, type StocksResponse, type Vcp } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: StocksResponse }
  | { kind: "error" };

const ALL = "__all__";
const VCP_ONLY = "vcp_only";
const VCP_NONE = "non_vcp";

/** The VCP badge tooltip: the server-built reason + pivot + invalidation note, rendered verbatim
 *  (never assembled client-side — single source of truth). */
function vcpTitle(vcp: Vcp): string {
  return [vcp.reason, vcp.pivot != null ? `Pivot $${vcp.pivot.toFixed(2)}.` : null, vcp.invalidation.note]
    .filter(Boolean)
    .join(" ");
}

// The six canonical setup statuses (fixed vocabulary so "Actionable" is always selectable, even
// when zero rows currently match — the journey then shows an explicit empty state).
const SETUP_STATUSES = [
  "Actionable",
  "Breakout-watch",
  "Pullback-watch",
  "Extended",
  "Avoid",
  "Risk-off-watchlist",
];

function setupVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "Actionable":
      return "ok";
    case "Breakout-watch":
    case "Pullback-watch":
      return "accent";
    case "Extended":
    case "Risk-off-watchlist":
      return "warn";
    case "Avoid":
      return "danger";
    default:
      return "default";
  }
}

export default function StocksPage() {
  const { asOf } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [sector, setSector] = useState<string>(ALL);
  const [setup, setSetup] = useState<string>(ALL);
  const [vcp, setVcp] = useState<string>(ALL);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchStocks(asOf ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

  const rows = state.kind === "ok" ? state.data.rows : [];

  // sectors present in the data, for the Sector filter (re-display of server rows only)
  const sectors = useMemo(
    () => Array.from(new Set(rows.map((r) => r.sector))).sort(),
    [rows],
  );

  // client-side FILTER only — never re-sorts or recomputes a score/flag (single source of truth).
  // The VCP filter narrows on the SERVER-computed `row.vcp.flagged` (pure re-display, no detection).
  const visible = useMemo(
    () =>
      rows.filter(
        (r) =>
          (sector === ALL || r.sector === sector) &&
          (setup === ALL || r.setup.status === setup) &&
          (vcp === ALL || (vcp === VCP_ONLY ? r.vcp.flagged : !r.vcp.flagged)),
      ),
    [rows, sector, setup, vcp],
  );

  return (
    <div className="space-y-4">
      <PageHeading
        title="Stocks"
        subtitle="Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason"
      />

      {state.kind === "ok" && rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="default" className="num">
            as of {state.data.asof_date}
          </Badge>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Sector
            <Select value={sector} onChange={(e) => setSector(e.target.value)} aria-label="Filter by sector">
              <option value={ALL}>All sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Setup
            <Select value={setup} onChange={(e) => setSetup(e.target.value)} aria-label="Filter by setup status">
              <option value={ALL}>All setups</option>
              {SETUP_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            VCP
            <Select value={vcp} onChange={(e) => setVcp(e.target.value)} aria-label="Filter by VCP pattern">
              <option value={ALL}>All</option>
              <option value={VCP_ONLY}>VCP only</option>
              <option value={VCP_NONE}>Non-VCP</option>
            </Select>
          </label>
          <span className="num text-xs text-text-faint">
            {visible.length} / {rows.length}
          </span>
        </div>
      ) : null}

      {state.kind === "loading" ? <StocksSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Stock Leaderboard could not load from the API. No rankings are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && rows.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title="No ranked stocks"
          description="The backend returned no stock rows for the current data date."
        />
      ) : null}

      {state.kind === "ok" && rows.length > 0 && visible.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title="No stocks match these filters"
          description={`${
            vcp === VCP_ONLY
              ? "No VCP-flagged name"
              : vcp === VCP_NONE
                ? "No non-VCP name"
                : "No stock"
          } is currently ${setup !== ALL ? `“${setup}”` : "shown"}${
            sector !== ALL ? ` in ${sector}` : ""
          }. No rows are fabricated to fill the view — clear a filter to see more.`}
        />
      ) : null}

      {state.kind === "ok" && visible.length > 0 ? (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Ticker</th>
                <th className="px-3 py-2 font-medium">Sector</th>
                <th className="px-3 py-2 font-medium">Leadership</th>
                <th className="px-3 py-2 font-medium">Entry Quality</th>
                <th className="px-3 py-2 font-medium">Risk</th>
                <th className="px-3 py-2 font-medium">Setup</th>
                <th className="px-3 py-2 font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <StockTableRow key={row.ticker} row={row} />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

function StockTableRow({ row }: { row: StockRow }) {
  return (
    <tr className="border-b border-border transition-colors hover:bg-surface-2">
      <td className="num px-3 py-2 text-text-faint">{row.rank}</td>
      <td className="px-3 py-2">
        <Link
          href={`/stocks/${row.ticker}`}
          className="num font-semibold text-accent hover:underline focus-visible:underline focus-visible:outline-none"
        >
          {row.ticker}
        </Link>
      </td>
      <td className="px-3 py-2 text-xs text-text-muted">{row.sector}</td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.leadership.bucket} score={row.leadership.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.entry_quality.bucket} score={row.entry_quality.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={row.risk.bucket} score={row.risk.score} invert />
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
          {row.vcp.flagged ? (
            <Badge variant="accent" className="cursor-help" title={vcpTitle(row.vcp)}>
              VCP
            </Badge>
          ) : null}
        </div>
      </td>
      <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
        <span className="line-clamp-2" title={row.setup.reason}>
          {row.setup.reason}
        </span>
      </td>
    </tr>
  );
}

function StocksSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
