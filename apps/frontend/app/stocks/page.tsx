"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, TrendingUp } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { InfoTooltip } from "@/components/ui/info-tooltip";
import { TermInfo } from "@/components/ui/term-info";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";
import {
  fetchMethodology,
  fetchStocks,
  type MethodologyCatalog,
  type StockRow,
  type StocksResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: StocksResponse }
  | { kind: "error" };

const ALL = "__all__";

/** A detected price pattern's read-only flag shape — every pattern (VCP + the iter-9 additions) shares
 *  this contract, so the leaderboard filters/renders them uniformly (no per-pattern branching). */
type PatternFlag = {
  flagged: boolean;
  reason: string;
  pivot: number | null;
  invalidation: { level: number | null; note: string };
};

/** The detected patterns shown on the leaderboard, in display order. Each maps the canonical config key
 *  (matches the /methodology catalog `key`) to its row field + a short badge label. Adding a pattern is
 *  ONE entry here — the badge, the filter, and the tooltip all read this list (config-driven UI). */
const PATTERNS: { key: string; label: string; badge: string; get: (row: StockRow) => PatternFlag }[] = [
  { key: "vcp", label: "VCP", badge: "VCP", get: (r) => r.vcp },
  { key: "pullback_to_rising_dma", label: "Pullback to rising DMA", badge: "Pullback", get: (r) => r.pullback_to_rising_dma },
  { key: "flat_base_breakout", label: "Flat-base breakout", badge: "Flat base", get: (r) => r.flat_base_breakout },
];

/** Decode the URL `pattern` query param into the leaderboard's internal filter value (J-31 deep-link).
 *  Strictly validated against the PATTERNS registry: `<key>__only` / `<key>__none` for a KNOWN key,
 *  else the `__all__` sentinel — an absent or unrecognized param never crashes and fabricates no filter
 *  (it harmlessly falls back to "all"). The encoding is the leaderboard's existing one verbatim; this is
 *  the ONLY place a URL param maps to filter state — no date/as_of param is ever read here (J-18). */
function parsePatternParam(raw: string | null): string {
  if (!raw) return ALL;
  const [key, mode] = raw.split("__");
  const known = PATTERNS.some((p) => p.key === key);
  if (known && (mode === "only" || mode === "none")) return `${key}__${mode}`;
  return ALL;
}

/** A pattern badge tooltip: the server-built reason + pivot + invalidation note, rendered verbatim
 *  (never assembled client-side — single source of truth). */
function patternTitle(flag: PatternFlag): string {
  return [flag.reason, flag.pivot != null ? `Pivot $${flag.pivot.toFixed(2)}.` : null, flag.invalidation.note]
    .filter(Boolean)
    .join(" ");
}

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

/** Thin wrapper providing the Suspense boundary that `useSearchParams()` requires in the Next 15 App
 *  Router (a production-build requirement). All hooks live in StocksInner, inside the boundary. */
export default function StocksPage() {
  return (
    <Suspense fallback={<StocksSkeleton />}>
      <StocksInner />
    </Suspense>
  );
}

function StocksInner() {
  const { asOf } = useAsOf();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [state, setState] = useState<State>({ kind: "loading" });
  // Filters init ONCE from the URL (lazy initializers — read on mount only). `sector`/`setup` are taken
  // verbatim (an unmatched value harmlessly renders the existing honest empty-state); `pattern` is
  // strictly validated against the PATTERNS registry. These three filter params are the ONLY URL state —
  // the as-of date stays in the global asof-provider (useAsOf), never a query param (J-18).
  const [sector, setSector] = useState<string>(() => searchParams.get("sector") ?? ALL);
  const [setup, setSetup] = useState<string>(() => searchParams.get("setup") ?? ALL);
  const [pattern, setPattern] = useState<string>(() => parsePatternParam(searchParams.get("pattern")));
  const [catalog, setCatalog] = useState<MethodologyCatalog | null>(null);

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

  // The config-backed Setup & Pattern catalog (iter-12) — fetched independently of the as-of date
  // (config is global) and NON-blocking: a failure must NOT break the leaderboard or its filters
  // (graceful degradation protects J-02 and warm load J-15). It drives the badge definition tooltips
  // and the Setup-filter vocabulary below.
  useEffect(() => {
    const controller = new AbortController();
    fetchMethodology(controller.signal)
      .then((data) => setCatalog(data))
      .catch(() => {
        if (!controller.signal.aborted) setCatalog(null);
      });
    return () => controller.abort();
  }, []);

  // Reflect filter changes OUT to the URL so the view is shareable / back-navigable — WITHOUT a server
  // refetch (the fetchStocks effect above stays keyed to [asOf] only; J-15 warm load unchanged). State is
  // initialized from the URL once above and never driven FROM searchParams, so there is no state↔URL loop.
  // The mount run is skipped so only real filter changes are written; `__all__` values are omitted for
  // clean URLs. NO date/as_of param is ever written here (J-18 — the as-of stays in the global provider).
  const didReflectMount = useRef(false);
  useEffect(() => {
    if (!didReflectMount.current) {
      didReflectMount.current = true;
      return;
    }
    const params = new URLSearchParams();
    if (sector !== ALL) params.set("sector", sector);
    if (setup !== ALL) params.set("setup", setup);
    if (pattern !== ALL) params.set("pattern", pattern);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [sector, setup, pattern, pathname, router]);

  const rows = state.kind === "ok" ? state.data.rows : [];

  // status -> catalog meaning (the SAME generic definition the /methodology page shows). The badge
  // tooltip renders this, NOT the per-row reason (which stays unchanged in the Reason column).
  const setupMeaning = useMemo(() => {
    const map = new Map<string, string>();
    catalog?.entries
      .filter((entry) => entry.kind === "setup")
      .forEach((entry) => map.set(entry.key, entry.meaning));
    return map;
  }, [catalog]);
  // pattern key -> catalog meaning (the SAME generic definition the /methodology page shows), for every
  // detected pattern. Keyed by config `key` so a new pattern's tooltip appears with no per-pattern code.
  const patternMeaning = useMemo(() => {
    const map = new Map<string, string>();
    catalog?.entries
      .filter((entry) => entry.kind === "pattern")
      .forEach((entry) => map.set(entry.key, entry.meaning));
    return map;
  }, [catalog]);
  // Setup-filter vocabulary: the catalog's setup entries in catalog order; graceful fallback to the
  // statuses present in the data if the catalog fetch failed (a catalog hiccup must NOT break J-02).
  const setupOptions = useMemo(() => {
    const fromCatalog = catalog?.entries
      .filter((entry) => entry.kind === "setup")
      .map((entry) => entry.key);
    if (fromCatalog && fromCatalog.length > 0) return fromCatalog;
    return Array.from(new Set(rows.map((row) => row.setup.status)));
  }, [catalog, rows]);

  // sectors present in the data, for the Sector filter (re-display of server rows only)
  const sectors = useMemo(
    () => Array.from(new Set(rows.map((r) => r.sector))).sort(),
    [rows],
  );

  // client-side FILTER only — never re-sorts or recomputes a score/flag (single source of truth). The
  // pattern filter narrows on the SERVER-computed `row.<name>.flagged` (pure re-display, no detection).
  // The `pattern` value is `__all__`, or `<key>__only` / `<key>__none` for a specific detected pattern.
  const visible = useMemo(() => {
    const [patternKey, patternMode] = pattern === ALL ? [null, null] : pattern.split("__");
    const patternEntry = patternKey ? PATTERNS.find((p) => p.key === patternKey) : null;
    return rows.filter((r) => {
      if (sector !== ALL && r.sector !== sector) return false;
      if (setup !== ALL && r.setup.status !== setup) return false;
      if (patternEntry) {
        const flagged = patternEntry.get(r).flagged;
        if (patternMode === "only" ? !flagged : flagged) return false;
      }
      return true;
    });
  }, [rows, sector, setup, pattern]);

  // a plain-language label for the active pattern filter, used only in the honest empty-state copy.
  const patternFilterLabel = useMemo(() => {
    if (pattern === ALL) return null;
    const [key, mode] = pattern.split("__");
    const entry = PATTERNS.find((p) => p.key === key);
    if (!entry) return null;
    return mode === "only" ? `${entry.label}-flagged` : `non-${entry.label}`;
  }, [pattern]);

  return (
    <div className="space-y-4">
      <PageHeading
        title="Stocks"
        subtitle="Stock Leaderboard — ranked by Leadership, with independent Entry Quality and Risk (danger) scores, a setup status and a reason"
      />

      {state.kind === "ok" && rows.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="default" className="num">
            as of {formatIsoDate(state.data.asof_date)}
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
              {setupOptions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-2 text-xs text-text-muted">
            Pattern
            <Select value={pattern} onChange={(e) => setPattern(e.target.value)} aria-label="Filter by detected pattern">
              <option value={ALL}>All patterns</option>
              {PATTERNS.map((p) => (
                <optgroup key={p.key} label={p.label}>
                  <option value={`${p.key}__only`}>{p.label} only</option>
                  <option value={`${p.key}__none`}>Not {p.label}</option>
                </optgroup>
              ))}
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
            patternFilterLabel ? `No ${patternFilterLabel} name` : "No stock"
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
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="Leadership Score">Leadership</TermInfo>
                </th>
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="Entry Quality Score">Entry Quality</TermInfo>
                </th>
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="Risk Score">Risk</TermInfo>
                </th>
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="setup status">Setup</TermInfo>
                </th>
                <th className="px-3 py-2 font-medium">
                  <TermInfo term="reason summary">Reason</TermInfo>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <StockTableRow
                  key={row.ticker}
                  row={row}
                  setupMeaning={setupMeaning.get(row.setup.status)}
                  patternMeaning={patternMeaning}
                />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

function StockTableRow({
  row,
  setupMeaning,
  patternMeaning,
}: {
  row: StockRow;
  setupMeaning?: string;
  patternMeaning: Map<string, string>;
}) {
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
          {setupMeaning ? (
            <InfoTooltip label={`Definition of ${row.setup.status}`} content={setupMeaning} />
          ) : null}
          {PATTERNS.filter((p) => p.get(row).flagged).map((p) => {
            const meaning = patternMeaning.get(p.key);
            return (
              <span key={p.key} className="inline-flex items-center gap-1">
                <Badge variant="accent" className="cursor-help" title={patternTitle(p.get(row))}>
                  {p.badge}
                </Badge>
                {meaning ? (
                  <InfoTooltip label={`Definition of the ${p.label} pattern`} content={meaning} />
                ) : null}
              </span>
            );
          })}
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
