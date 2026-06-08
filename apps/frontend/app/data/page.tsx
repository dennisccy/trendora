"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Database,
  KeyRound,
  Loader2,
  Play,
  RotateCcw,
  Search,
  Trash2,
  X,
} from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  executeDataRemoval,
  fetchDataCoverage,
  fetchDataJob,
  previewDataRemoval,
  resumeDataJob,
  startDataJob,
  type DataJob,
  type DataJobKind,
  type DataOverviewResponse,
  type DataRun,
  type PerSymbolCoverage,
  type ProviderSource,
  type RemovePreview,
  type RemoveScope,
  type ResumableImport,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: DataOverviewResponse }
  | { kind: "error" };

const FIELD =
  "h-9 rounded-md border border-border bg-surface-2 px-3 text-sm text-text placeholder:text-text-faint " +
  "transition-colors hover:border-border-strong focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent " +
  "disabled:cursor-not-allowed disabled:opacity-50";

/** Job/run status -> palette token (DESIGN SYSTEM): ok green, partial/resumable amber, failed red,
 *  running teal. `resumable` (J-34: a rate-limited graceful pause) is amber `--warn` — explicitly
 *  DISTINCT from red `--neg` `failed`. */
function statusVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "ok":
      return "ok";
    case "partial":
    case "resumable":
      return "warn";
    case "failed":
      return "danger";
    case "running":
      return "accent";
    default:
      return "default";
  }
}

function fmtDate(value: string | null): string {
  return value ? value : "—";
}

export default function DataManagerPage() {
  const { refresh } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [kind, setKind] = useState<DataJobKind>("backfill");
  // J-33: the chosen import source id + the SESSION-ONLY pasted key. `apiKey` lives in component memory
  // ONLY — it is NEVER written to localStorage, the URL, or a cookie, and is cleared on job completion /
  // unmount. The picker is config-driven (populated from `data.sources`) — no hardcoded provider list.
  const [source, setSource] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [job, setJob] = useState<DataJob | null>(null);
  const [starting, setStarting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const prefilled = useRef(false);

  const sources: ProviderSource[] = state.kind === "ok" ? state.data.sources : [];
  const selectedSource = sources.find((s) => s.id === source);
  const isExpandKind = kind === "expand";
  // Both a fetch/both AND an expand pull from a live import source (expand fetches OHLCV + a market cap).
  const isFetchKind = kind === "fetch" || kind === "both" || isExpandKind;
  // J-35 eligibility: an expand needs a market-cap-capable source. An ineligible source is disabled in the
  // picker; if the selected source is ineligible for expand, the Start button is blocked (UI guard mirrors
  // the backend gate). `supports_market_cap` comes from the config-driven `sources` catalog (no hardcoding).
  const sourceIneligibleForExpand = isExpandKind && Boolean(selectedSource) && !selectedSource?.supports_market_cap;
  // Reveal the session-only key field only for a needs-key source with no env key (an available source
  // already has its key in the environment — no paste needed).
  const keyFieldVisible = isFetchKind && Boolean(selectedSource?.needs_key) && selectedSource?.available === false;

  const loadOverview = useCallback((signal?: AbortSignal) => {
    fetchDataCoverage(signal)
      .then((data) => {
        setState({ kind: "ok", data });
        // Prefill the range ONCE from the actual backfill gaps so the default Start is a valid,
        // gap-creating job (the date inputs are job PARAMETERS — they never touch the as-of switcher).
        if (!prefilled.current) {
          const gaps = data.coverage.gaps_preview;
          if (gaps.length > 0) {
            setStart(gaps[0]);
            setEnd(gaps[Math.min(4, gaps.length - 1)]);
            prefilled.current = true;
          }
        }
      })
      .catch(() => {
        if (!signal?.aborted) setState({ kind: "error" });
      });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadOverview(controller.signal);
    return () => controller.abort();
  }, [loadOverview]);

  // Default the import source to the first catalog entry (the config default_source, no-key) once the
  // catalog loads — the picker is populated from config, never a hardcoded provider list.
  useEffect(() => {
    if (!source && sources.length > 0) setSource(sources[0].id);
  }, [sources, source]);

  // The session-only key never outlives the component: clear it on unmount (defence in depth — React
  // also discards the state). Never persisted to localStorage / URL / cookie.
  useEffect(() => () => setApiKey(""), []);

  // Poll the active job until it leaves `running`; on completion, refresh the global as-of run list
  // (so new dates are selectable WITHOUT a hard reload) and reload coverage + run history. Keyed on
  // the job id + status (primitives) so the interval is created once per run, not re-armed each tick.
  const jobId = job?.job_id ?? null;
  const jobStatus = job?.status ?? null;
  useEffect(() => {
    if (!jobId || jobStatus !== "running") return;
    let active = true;
    const timer = setInterval(() => {
      fetchDataJob(jobId)
        .then((snap) => {
          if (!active) return;
          setJob(snap);
          if (snap.status !== "running") {
            clearInterval(timer);
            setApiKey(""); // J-33: drop the session-only key as soon as the job finishes
            refresh();
            loadOverview();
          }
        })
        .catch(() => {
          /* transient poll error — keep polling; a persistent failure surfaces in the job card */
        });
    }, 1000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [jobId, jobStatus, refresh, loadOverview]);

  const jobRunning = jobStatus === "running";

  // J-34: pull a freshly-resumed import into the job card. The poll effect (keyed on job id + status)
  // picks it up because its status is "running" again; on completion it reloads coverage + the
  // resumable-imports list (the completed import drops off), exactly like a freshly-started job.
  const onResumed = useCallback((importId: string) => {
    fetchDataJob(importId)
      .then((snap) => setJob(snap))
      .catch(() => {
        /* the resume POST already surfaced any error; ignore a transient fetch race */
      });
  }, []);

  async function handleStart(event: React.FormEvent) {
    event.preventDefault();
    if (!start || !end || starting || jobRunning) return;
    // J-35 UI guard: never start an expand over a source that cannot supply market cap (the backend also
    // rejects it with a 400 — this surfaces the reason BEFORE the request).
    if (sourceIneligibleForExpand) {
      setFormError("This source cannot supply market cap — not selectable for an expand job.");
      return;
    }
    setStarting(true);
    setFormError(null);
    try {
      // Send the chosen source only when the job fetches; send the SESSION-ONLY key only when the paste
      // field is shown and non-blank (omitted otherwise so a stale key is never transmitted).
      const opts = isFetchKind
        ? { source: source || undefined, api_key: keyFieldVisible ? apiKey || undefined : undefined }
        : undefined;
      const resp = await startDataJob(kind, start, end, opts);
      const snap = await fetchDataJob(resp.job_id); // initial progress snapshot
      setJob(snap);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not start the job.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeading
        title="Data Manager"
        subtitle="Grow the dataset on demand — view coverage and gaps, then fetch real EOD history and/or backfill immutable snapshots by date or range. Jobs run asynchronously; new snapshot dates become selectable in the global as-of switcher and grow the Backtest evidence."
      />

      {state.kind === "loading" ? <DataSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              Dataset coverage could not load from the API. No figures are shown rather than fabricated
              values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? (
        <>
          <CoveragePanel data={state.data} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <JobForm
              start={start}
              end={end}
              kind={kind}
              setStart={setStart}
              setEnd={setEnd}
              setKind={setKind}
              sources={sources}
              source={source}
              setSource={setSource}
              showSource={isFetchKind}
              isExpandKind={isExpandKind}
              sourceIneligibleForExpand={sourceIneligibleForExpand}
              apiKey={apiKey}
              setApiKey={setApiKey}
              keyFieldVisible={keyFieldVisible}
              selectedSource={selectedSource}
              onStart={handleStart}
              busy={starting}
              running={Boolean(jobRunning)}
              error={formError}
            />
            <JobProgressPanel job={job} sources={sources} onResumed={onResumed} />
          </div>
          <ResumableImportsPanel
            imports={state.data.resumable_imports}
            sources={sources}
            onResumed={onResumed}
          />
          <RemoveDataPanel
            onRemoved={() => {
              refresh(); // the removed dates drop out of the global as-of switcher
              loadOverview(); // re-read coverage + the per-symbol table (now smaller)
            }}
          />
          <RunHistoryPanel runs={state.data.runs} />
        </>
      ) : null}
    </div>
  );
}

function PanelTitle({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="border-b border-border px-4 py-3">
      <h2 className="text-sm font-semibold text-text">{children}</h2>
      {hint ? <p className="mt-0.5 text-xs text-text-faint">{hint}</p> : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="space-y-0.5">
      <p className="text-xs uppercase tracking-wide text-text-faint">{label}</p>
      <p className="num text-sm text-text">{value}</p>
    </div>
  );
}

/** A single coverage figure shown NEXT TO its one-line plain-language definition (J-36) — so a reader
 *  never sees a bare number. The value is read verbatim from the backend payload (no recompute here). */
function DefinedMetric({
  label,
  value,
  definition,
  testId,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  definition: string;
  testId?: string;
  tone?: string;
}) {
  return (
    <div className="space-y-1 rounded-md border border-border bg-surface-2 p-3">
      <p className="text-xs uppercase tracking-wide text-text-faint">{label}</p>
      <p className={cn("num text-lg font-semibold text-text", tone)} data-testid={testId}>
        {value}
      </p>
      <p className="text-xs leading-snug text-text-muted">{definition}</p>
    </div>
  );
}

function CoveragePanel({ data }: { data: DataOverviewResponse }) {
  const c = data.coverage;
  return (
    <Card className="p-0">
      <PanelTitle hint="Descriptive metadata read from the dataset — not a recomputed score or return. Each figure is shown with its plain-language definition.">
        Dataset coverage
      </PanelTitle>
      <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
        <DefinedMetric
          label="Price history"
          value={`${fmtDate(c.price_start)} → ${fmtDate(c.price_end)}`}
          definition="The earliest and latest dates with any stored daily price bar."
        />
        <DefinedMetric
          label="Universe"
          testId="universe-count-defined"
          value={<span data-testid="universe-count">{c.universe_count}</span>}
          definition="The config-screened, SCORED names (the liquidity/price/market-cap screen result). This is the universe — distinct from symbols below."
        />
        <DefinedMetric
          label="Symbols"
          value={c.symbol_count}
          definition="Every ticker with stored bars — including the index/sector/industry ETFs and ^VIX, which are NOT scored universe members."
        />
        <DefinedMetric
          label="Trading days"
          value={c.trading_day_count}
          definition="Distinct dates the benchmark (SPY) has a bar — the trading calendar the scanner and walk-forward use."
        />
        <DefinedMetric
          label="Snapshot dates"
          value={c.snapshot_count}
          definition="Trading days with a stored immutable scanner snapshot (an as-of date selectable in the global switcher)."
        />
        <DefinedMetric
          label="Backfill gaps"
          tone={c.gap_count > 0 ? "text-warn" : "text-pos"}
          value={c.gap_count}
          definition="A backfill gap is a trading day that HAS bars but NO scanner snapshot — the actionable backfill targets."
        />
      </div>
      <p className="border-t border-border px-4 py-2 text-xs text-text-muted">
        <span className="font-medium text-text-muted">Universe vs symbols: </span>
        the <span className="text-text">universe</span> ({c.universe_count}) is the set of config-screened,
        scored names; <span className="text-text">symbols</span> ({c.symbol_count}) is every ticker with
        bars, which additionally includes the benchmark/sector/industry ETFs and <span className="num">^VIX</span>.
        {c.gap_count > 0 ? (
          <>
            {" "}
            <span className="text-text-faint">Gap range: </span>
            <span className="num">{fmtDate(c.gap_first)} → {fmtDate(c.gap_last)}</span>.
          </>
        ) : (
          " Every trading day with bars already has an immutable snapshot — no backfill gaps."
        )}
      </p>
      <PerSymbolCoverageTable rows={c.per_symbol} symbolCount={c.symbol_count} universeCount={c.universe_count} />
    </Card>
  );
}

/** J-36 per-symbol / per-universe-member coverage table: one row per stored symbol AND per universe
 *  member, with in-universe / has-data / date-range / bar-count / thin-or-missing. Sorting + filtering are
 *  UI-only (the page re-formats backend values — it computes no coverage figure). A universe-members-only
 *  filter confirms every member shows data-or-missing (none silently absent). Thin/missing get an amber/
 *  muted treatment. The displayed distinct-symbol (has-data) count == symbol_count and the in-universe
 *  count == universe_count (the same backend source — they can never drift). */
function PerSymbolCoverageTable({
  rows,
  symbolCount,
  universeCount,
}: {
  rows: PerSymbolCoverage[];
  symbolCount: number;
  universeCount: number;
}) {
  const [query, setQuery] = useState("");
  const [membersOnly, setMembersOnly] = useState(false);
  const [sortKey, setSortKey] = useState<"symbol" | "bar_count">("symbol");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const filtered = useMemo(() => {
    const q = query.trim().toUpperCase();
    let out = rows.filter((r) => (membersOnly ? r.in_universe : true));
    if (q) out = out.filter((r) => r.symbol.toUpperCase().includes(q));
    const sorted = [...out].sort((a, b) => {
      let cmp: number;
      if (sortKey === "bar_count") cmp = a.bar_count - b.bar_count;
      else cmp = a.symbol.localeCompare(b.symbol);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [rows, query, membersOnly, sortKey, sortDir]);

  // UI-side counts mirror the backend aggregates (read from the same per_symbol payload) — the table can
  // never present a count that drifts from the definitions block above.
  const distinctWithData = useMemo(() => rows.filter((r) => r.has_data).length, [rows]);
  const inUniverseRows = useMemo(() => rows.filter((r) => r.in_universe).length, [rows]);

  function toggleSort(key: "symbol" | "bar_count") {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir(key === "bar_count" ? "desc" : "asc");
    }
  }

  return (
    <div className="border-t border-border" data-testid="per-symbol-coverage">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="space-y-0.5">
          <h3 className="text-sm font-semibold text-text">Per-symbol coverage</h3>
          <p className="text-xs text-text-faint">
            One row per stored symbol and per universe member. In-universe rows:{" "}
            <span className="num text-text-muted" data-testid="table-in-universe-count">
              {inUniverseRows}
            </span>{" "}
            (= universe {universeCount}) · with-data rows:{" "}
            <span className="num text-text-muted" data-testid="table-with-data-count">
              {distinctWithData}
            </span>{" "}
            (= symbols {symbolCount}).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="relative flex items-center">
            <Search className="pointer-events-none absolute left-2 h-3.5 w-3.5 text-text-faint" aria-hidden />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Filter symbols"
              placeholder="Filter symbol…"
              className={cn(FIELD, "num h-8 w-40 pl-7 text-xs")}
            />
          </label>
          <button
            type="button"
            onClick={() => setMembersOnly((v) => !v)}
            aria-pressed={membersOnly}
            data-testid="universe-members-only-toggle"
            className={cn(
              "inline-flex h-8 items-center gap-1.5 rounded-md border px-3 text-xs font-medium transition",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              membersOnly
                ? "border-accent bg-surface-2 text-accent"
                : "border-border bg-surface-2 text-text-muted hover:border-border-strong",
            )}
          >
            Universe members only
          </button>
        </div>
      </div>
      <div className="max-h-96 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 bg-surface">
            <tr className="border-y border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="px-3 py-2 font-medium">
                <SortHeader label="Symbol" active={sortKey === "symbol"} dir={sortDir} onClick={() => toggleSort("symbol")} />
              </th>
              <th className="px-3 py-2 font-medium">In universe</th>
              <th className="px-3 py-2 font-medium">Has data</th>
              <th className="px-3 py-2 font-medium">Date range</th>
              <th className="px-3 py-2 text-right font-medium">
                <SortHeader label="Bars" active={sortKey === "bar_count"} dir={sortDir} onClick={() => toggleSort("bar_count")} right />
              </th>
              <th className="px-3 py-2 font-medium">Flag</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-xs text-text-muted">
                  No symbols match the current filter.
                </td>
              </tr>
            ) : (
              filtered.map((r) => (
                <tr
                  key={r.symbol}
                  data-testid="coverage-row"
                  data-symbol={r.symbol}
                  className={cn(
                    "border-b border-border last:border-b-0 hover:bg-surface-2",
                    r.missing || r.thin ? "bg-surface-2" : null,
                  )}
                >
                  <td className="num px-3 py-1.5 font-medium text-text">{r.symbol}</td>
                  <td className="px-3 py-1.5">
                    {r.in_universe ? (
                      <Badge variant="accent">universe</Badge>
                    ) : (
                      <span className="text-xs text-text-faint">ETF / index</span>
                    )}
                  </td>
                  <td className="px-3 py-1.5">
                    {r.has_data ? (
                      <span className="text-xs text-pos">yes</span>
                    ) : (
                      <span className="text-xs text-text-faint">no</span>
                    )}
                  </td>
                  <td className="num px-3 py-1.5 text-xs text-text-muted">
                    {r.has_data ? `${fmtDate(r.first)} → ${fmtDate(r.last)}` : <span className="text-text-faint">NA</span>}
                  </td>
                  <td className="num px-3 py-1.5 text-right text-text-muted">{r.bar_count}</td>
                  <td className="px-3 py-1.5">
                    {r.missing ? (
                      <Badge variant="warn">missing</Badge>
                    ) : r.thin ? (
                      <Badge variant="warn">thin</Badge>
                    ) : (
                      <span className="text-xs text-text-faint">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="border-t border-border px-4 py-2 text-xs text-text-faint">
        <span className="text-warn">thin</span> = has some bars but fewer than the config history threshold
        (insufficient for full analysis); <span className="text-warn">missing</span> = a universe member with
        no stored bars (shown NA, never a fabricated range).
      </p>
    </div>
  );
}

function SortHeader({
  label,
  active,
  dir,
  onClick,
  right,
}: {
  label: string;
  active: boolean;
  dir: "asc" | "desc";
  onClick: () => void;
  right?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 uppercase tracking-wide transition hover:text-text",
        right ? "flex-row-reverse" : null,
        active ? "text-text" : "text-text-faint",
      )}
    >
      {label}
      <span aria-hidden className="text-[0.6rem]">{active ? (dir === "asc" ? "▲" : "▼") : "↕"}</span>
    </button>
  );
}

function JobForm({
  start,
  end,
  kind,
  setStart,
  setEnd,
  setKind,
  sources,
  source,
  setSource,
  showSource,
  isExpandKind,
  sourceIneligibleForExpand,
  apiKey,
  setApiKey,
  keyFieldVisible,
  selectedSource,
  onStart,
  busy,
  running,
  error,
}: {
  start: string;
  end: string;
  kind: DataJobKind;
  setStart: (v: string) => void;
  setEnd: (v: string) => void;
  setKind: (v: DataJobKind) => void;
  sources: ProviderSource[];
  source: string;
  setSource: (v: string) => void;
  showSource: boolean;
  isExpandKind: boolean;
  sourceIneligibleForExpand: boolean;
  apiKey: string;
  setApiKey: (v: string) => void;
  keyFieldVisible: boolean;
  selectedSource: ProviderSource | undefined;
  onStart: (e: React.FormEvent) => void;
  busy: boolean;
  running: boolean;
  error: string | null;
}) {
  // Start is blocked while busy/running, with no dates, OR (J-35) when an expand is aimed at a source that
  // cannot supply market cap — the backend rejects that too; the UI blocks it up front with a reason.
  const disabled = busy || running || !start || !end || sourceIneligibleForExpand;
  return (
    <Card className="p-0">
      <PanelTitle hint="Pick a date or range, a job kind, and — for a fetch or expand — an import source. These date inputs are job parameters — they do NOT change the global as-of viewing date.">
        Start a fetch / backfill / expand job
      </PanelTitle>
      <form onSubmit={onStart} className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Start date
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              aria-label="Job start date"
              className={cn(FIELD, "num w-40")}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            End date
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              aria-label="Job end date"
              className={cn(FIELD, "num w-40")}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Job kind
            <Select
              aria-label="Job kind"
              className="w-44"
              value={kind}
              onChange={(e) => setKind(e.target.value as DataJobKind)}
            >
              <option value="backfill">Backfill snapshots</option>
              <option value="fetch">Fetch EOD prices</option>
              <option value="both">Fetch + backfill</option>
              <option value="expand">Expand universe</option>
            </Select>
          </label>
          {showSource ? (
            <label className="flex flex-col gap-1 text-xs text-text-muted">
              Import source
              <Select
                aria-label="Import source"
                className="w-52"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                {sources.map((s) => {
                  // J-35: for an expand, a source that cannot supply market cap is DISABLED with a reason
                  // (read from the config-driven `supports_market_cap` flag — never hardcoded).
                  const ineligible = isExpandKind && !s.supports_market_cap;
                  return (
                    <option key={s.id} value={s.id} disabled={ineligible}>
                      {s.label}
                      {ineligible
                        ? " · cannot supply market cap — not selectable for expand"
                        : ` · ${s.available ? "available" : "needs key"}`}
                    </option>
                  );
                })}
              </Select>
            </label>
          ) : null}
          <button
            type="submit"
            disabled={disabled}
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-bg",
              "transition hover:brightness-110 active:brightness-95",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            {busy || running ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Play className="h-4 w-4" aria-hidden />
            )}
            {running ? "Job running…" : "Start"}
          </button>
        </div>

        {showSource && selectedSource ? (
          <p className="text-xs text-text-muted" data-testid="source-availability">
            <span className="text-text-faint">{selectedSource.label}: </span>
            <span className={selectedSource.available ? "text-pos" : "text-warn"}>
              {selectedSource.available ? "available" : "needs key"}
            </span>
            <span className="text-text-faint"> · {selectedSource.reason}</span>
          </p>
        ) : null}

        {sourceIneligibleForExpand && selectedSource ? (
          <p
            role="alert"
            className="flex items-center gap-2 rounded-md border border-warn bg-surface-2 p-2 text-xs text-warn"
            data-testid="expand-ineligible-reason"
          >
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {selectedSource.label} cannot supply market cap — not selectable for an expand job. Pick a
            market-cap-capable source (e.g. Yahoo).
          </p>
        ) : null}

        {keyFieldVisible ? (
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            <span className="flex items-center gap-1.5">
              <KeyRound className="h-3.5 w-3.5 text-warn" aria-hidden />
              Session API key for {selectedSource?.label}
            </span>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              aria-label="Session API key"
              autoComplete="off"
              placeholder={selectedSource?.env_var ? `or set $${selectedSource.env_var}` : "paste a key"}
              className={cn(FIELD, "w-80")}
            />
            <span className="text-text-faint">
              Held in memory for this run only — never written to disk, the database, the run log, or a
              cookie, and never echoed back.
            </span>
          </label>
        ) : null}

        <p className="text-xs text-text-faint">
          Backfill creates immutable snapshots (and their forward returns) for trading days that have
          bars but no snapshot — offline and deterministic. Fetch pulls real EOD prices via the selected
          import source. Expand screens the committed candidate pool (the config liquidity/price/market-cap
          screen) over a market-cap-capable source and grows the scored universe — every omitted candidate
          is listed with its reason. A provider failure is surfaced explicitly and fabricates nothing.
        </p>
        {error ? (
          <p role="alert" className="flex items-center gap-2 text-sm text-neg">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
            {error}
          </p>
        ) : null}
      </form>
    </Card>
  );
}

function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-surface-2" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-2 rounded bg-accent transition-all" style={{ width: `${pct}%` }} />
    </div>
  );
}

function JobProgressPanel({
  job,
  sources,
  onResumed,
}: {
  job: DataJob | null;
  sources: ProviderSource[];
  onResumed: (importId: string) => void;
}) {
  if (!job) {
    return (
      <Card className="p-0">
        <PanelTitle>Job progress</PanelTitle>
        <p className="px-4 py-6 text-sm text-text-muted">
          No job has been started this session. Start a fetch or backfill job to watch its live progress
          and final summary here.
        </p>
      </Card>
    );
  }

  const isExpand = job.kind === "expand";
  // An expand fetches OHLCV in chunks (shows the symbols-fetched bar) AND then screens; a fetch/both shows
  // the fetch bar; a backfill shows the snapshot bar. The expand screen-result block is additional.
  const showFetch = job.kind === "fetch" || job.kind === "both" || isExpand;
  const showBackfill = job.kind === "backfill" || job.kind === "both";
  const paused = job.status === "resumable"; // J-34: a rate-limited graceful pause (amber, not failed)
  const failed = job.status === "failed" || job.status === "partial";
  const chunkTotal = job.chunk_total ?? 0;
  const symbolsRemaining = Math.max(job.symbols_total - job.symbols_ok - job.symbols_failed, 0);
  const jobSource = sources.find((s) => s.id === job.source);

  return (
    <Card className="p-0">
      <PanelTitle
        hint={`${job.kind} job · ${job.source ? `${job.source} · ` : ""}${job.start} → ${job.end}`}
      >
        Job progress
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={statusVariant(job.status)} className="num gap-1.5">
            {job.status === "running" ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
            {paused ? "rate-limited — resumable" : job.status}
          </Badge>
          {chunkTotal > 0 ? (
            <Badge variant="default" className="num gap-1" data-testid="chunk-progress">
              chunk {job.chunk_index ?? 0}/{chunkTotal}
            </Badge>
          ) : null}
          <span className="num text-xs text-text-muted">{job.message}</span>
        </div>

        {paused ? (
          <div
            className="space-y-2 rounded-md border border-warn bg-surface-2 p-3"
            data-testid="resumable-state"
          >
            <p className="flex items-center gap-1.5 text-xs font-medium text-warn">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
              Rate-limited — paused at chunk {job.chunk_index ?? 0}/{chunkTotal}. Progress is saved; resume
              to continue from the next un-fetched chunk (no data is re-fetched or duplicated).
            </p>
            <p className="num text-xs text-text-muted">
              <span className="text-pos">{job.symbols_ok} done</span>
              <span className="text-text-faint"> · </span>
              <span className="text-warn">{symbolsRemaining} remaining</span>
              {job.symbols_failed > 0 ? (
                <>
                  <span className="text-text-faint"> · </span>
                  <span className="text-neg">{job.symbols_failed} failed</span>
                </>
              ) : null}
            </p>
            <ResumeControl importId={job.job_id} source={jobSource} onResumed={onResumed} />
          </div>
        ) : null}

        {showFetch ? (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <span>Symbols fetched</span>
              <span className="num">
                {job.symbols_ok + job.symbols_failed}/{job.symbols_total}{" "}
                <span className="text-pos">({job.symbols_ok} ok</span>
                <span className="text-neg">, {job.symbols_failed} failed)</span>
              </span>
            </div>
            <ProgressBar done={job.symbols_ok + job.symbols_failed} total={job.symbols_total} />
            <p className="num text-xs text-text-faint">{job.bars_fetched} new price bars</p>
          </div>
        ) : null}

        {showBackfill ? (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <span>Snapshots backfilled</span>
              <span className="num">
                {job.dates_done}/{job.dates_total} dates
              </span>
            </div>
            <ProgressBar done={job.dates_done} total={job.dates_total} />
            <p className="num text-xs text-text-faint">
              {job.snapshots_created} snapshots · {job.forward_returns_inserted} forward returns inserted
            </p>
          </div>
        ) : null}

        {isExpand ? <ExpandScreenResult job={job} /> : null}

        {job.errors.length > 0 ? (
          <div className={cn("rounded-md border p-3 text-xs", failed ? "border-neg" : "border-warn")}>
            <p className={cn("mb-1 flex items-center gap-1.5 font-medium", failed ? "text-neg" : "text-warn")}>
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
              {job.errors.length} error{job.errors.length === 1 ? "" : "s"} (no data fabricated)
            </p>
            <ul className="space-y-0.5 text-text-muted">
              {job.errors.slice(0, 5).map((err, i) => (
                <li key={i} className="num truncate" title={err}>
                  {err}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

/** J-35 expand screen result on the job card: the passers count + the omitted-with-reason list (each
 *  candidate the config screen omitted, with its plain-language reason — e.g. "market_cap … < …",
 *  "no_market_cap", "price … < …"). Read-only descriptive job-control metadata served on the job snapshot;
 *  the universe value itself reads from the Coverage `universe-count` (single source — no second display). */
function ExpandScreenResult({ job }: { job: DataJob }) {
  const passers = job.passers ?? 0;
  const omittedTotal = job.omitted_total ?? 0;
  const omitted = job.omitted ?? [];
  return (
    <div className="space-y-2" data-testid="expand-screen-result">
      <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        <span>Universe screen</span>
        <Badge variant="ok" className="num gap-1" data-testid="expand-passers">
          {passers} passed
        </Badge>
        <Badge variant={omittedTotal > 0 ? "warn" : "default"} className="num gap-1" data-testid="expand-omitted-count">
          {omittedTotal} omitted
        </Badge>
        <span className="num text-text-faint">of {job.symbols_total} candidates</span>
      </div>
      {omitted.length > 0 ? (
        <div className="rounded-md border border-border bg-surface-2 p-3" data-testid="expand-omitted-list">
          <p className="mb-1 text-xs font-medium text-text-muted">
            Omitted candidates (each with its reason — never fabricated)
            {omittedTotal > omitted.length ? (
              <span className="text-text-faint"> · showing {omitted.length} of {omittedTotal}</span>
            ) : null}
          </p>
          <ul className="max-h-48 space-y-0.5 overflow-y-auto text-xs">
            {omitted.map((o, i) => (
              <li key={`${o.symbol}-${i}`} className="flex items-baseline justify-between gap-3">
                <span className="num font-medium text-text">{o.symbol}</span>
                <span className="num truncate text-right text-warn" title={o.reason}>
                  {o.reason}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : passers > 0 ? (
        <p className="text-xs text-text-faint">All screened candidates passed — no omissions.</p>
      ) : null}
    </div>
  );
}

/** J-34 Resume control: a Resume button that re-POSTs to the resume endpoint, re-prompting for the
 *  SESSION-ONLY key (type="password", held in component memory only, cleared right after submit) when
 *  the source needs one and it is not already in the environment. Used both on the live job card and on
 *  each post-restart resumable-imports row. */
function ResumeControl({
  importId,
  source,
  onResumed,
}: {
  importId: string;
  source: ProviderSource | undefined;
  onResumed: (importId: string) => void;
}) {
  // A key is needed only for a needs-key source with no env key (an available source already has its key
  // in the environment — the backend reads it; no paste needed). Mirrors the JobForm key-field logic.
  const needsKey = Boolean(source?.needs_key) && source?.available === false;
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleResume() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await resumeDataJob(importId, needsKey ? { api_key: apiKey || undefined } : undefined);
      setApiKey(""); // drop the session-only key the instant the resume is submitted
      onResumed(importId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resume the import.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      {needsKey ? (
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          <span className="flex items-center gap-1.5">
            <KeyRound className="h-3.5 w-3.5 text-warn" aria-hidden />
            Session API key for {source?.label}
          </span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            aria-label={`Session API key to resume ${importId}`}
            autoComplete="off"
            placeholder={source?.env_var ? `or set $${source.env_var}` : "paste a key"}
            className={cn(FIELD, "w-72")}
          />
        </label>
      ) : null}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={handleResume}
          disabled={busy}
          data-testid="resume-button"
          className={cn(
            "inline-flex h-8 items-center gap-1.5 rounded-md bg-warn px-3 text-xs font-semibold text-bg",
            "transition hover:brightness-110 active:brightness-95",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-warn focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
          )}
          Resume
        </button>
        {error ? (
          <span role="alert" className="text-xs text-neg">
            {error}
          </span>
        ) : null}
      </div>
    </div>
  );
}

/** J-34 post-restart resumable-imports surface: the paused imports from GET /api/data (durable
 *  checkpoints surviving a backend restart, even with no live in-memory job). Each row shows its source,
 *  range, chunk x/N, and symbols done/remaining, with a Resume button. Hidden when there are none. */
function ResumableImportsPanel({
  imports,
  sources,
  onResumed,
}: {
  imports: ResumableImport[];
  sources: ProviderSource[];
  onResumed: (importId: string) => void;
}) {
  if (imports.length === 0) return null; // empty list hidden (no clutter when nothing is paused)
  return (
    <Card className="p-0" data-testid="resumable-imports">
      <PanelTitle hint="Rate-limited imports paused mid-run — progress is saved to the database and survives a backend restart. Resume continues from the next un-fetched chunk; nothing is re-fetched or duplicated.">
        Resumable imports
      </PanelTitle>
      <ul className="divide-y divide-border">
        {imports.map((imp) => {
          const impSource = sources.find((s) => s.id === imp.source);
          return (
            <li key={imp.import_id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="warn" className="num gap-1">
                    chunk {imp.chunk_index}/{imp.chunk_total}
                  </Badge>
                  <span className="text-sm font-medium text-text">{impSource?.label ?? imp.source}</span>
                  <span className="num text-xs text-text-faint">
                    {imp.start} → {imp.end}
                  </span>
                </div>
                <p className="num text-xs text-text-muted">
                  <span className="text-pos">{imp.symbols_ok} done</span>
                  <span className="text-text-faint"> · </span>
                  <span className="text-warn">{imp.symbols_remaining} remaining</span>
                  {imp.symbols_failed > 0 ? (
                    <>
                      <span className="text-text-faint"> · </span>
                      <span className="text-neg">{imp.symbols_failed} failed</span>
                    </>
                  ) : null}
                  <span className="text-text-faint"> · {imp.bars_fetched} bars so far</span>
                </p>
              </div>
              <ResumeControl importId={imp.import_id} source={impSource} onResumed={onResumed} />
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

/** J-39 seed-safe Remove-data control. Pick a scope (by symbol and/or date range — these are ACTION
 *  PARAMETERS, NOT the global as-of viewing control), then a confirm-preview enumerates exactly which
 *  user-added bars would be removed (count + range), which are NOT removable (committed seed, with the
 *  reason), and the cascade of dependent snapshot/forward-return rows — BEFORE any deletion. A wholly-seed
 *  scope is refused (the confirm is disabled with the explicit reason). Confirming dispatches the
 *  destructive removal; afterward the page re-reads coverage and the as-of switcher reflects the smaller
 *  dataset. The "dialog" is an in-page modal built from Card + an overlay (there is no Dialog primitive). */
function RemoveDataPanel({ onRemoved }: { onRemoved: () => void }) {
  const [symbolsText, setSymbolsText] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [preview, setPreview] = useState<RemovePreview | null>(null);
  const [loading, setLoading] = useState(false); // preview in-flight
  const [removing, setRemoving] = useState(false); // destructive removal in-flight
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<RemovePreview | null>(null);

  function buildScope(): RemoveScope {
    const symbols = symbolsText
      .split(/[\s,]+/)
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);
    const scope: RemoveScope = {};
    if (symbols.length > 0) scope.symbols = symbols;
    if (start) scope.start = start;
    if (end) scope.end = end;
    return scope;
  }

  const hasScope = symbolsText.trim().length > 0 || Boolean(start) || Boolean(end);

  async function handlePreview() {
    if (!hasScope || loading) return;
    setLoading(true);
    setError(null);
    setDone(null);
    try {
      const result = await previewDataRemoval(buildScope());
      setPreview(result); // opens the confirm-preview modal
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not preview the removal.");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (!preview || preview.refused || removing) return;
    setRemoving(true);
    setError(null);
    try {
      const result = await executeDataRemoval(buildScope());
      setPreview(null);
      setDone(result);
      setSymbolsText("");
      setStart("");
      setEnd("");
      onRemoved(); // re-read coverage + refresh the as-of switcher (smaller dataset)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the data.");
    } finally {
      setRemoving(false);
    }
  }

  return (
    <Card className="p-0" data-testid="remove-data">
      <PanelTitle hint="Delete imported (user-added) data beyond the committed seed, by symbol and/or date range. A confirm-preview shows exactly what will be removed first. These date inputs are action parameters — they do NOT change the global as-of viewing date. The committed seed is never deletable.">
        Remove imported data
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Symbols (optional, comma/space separated)
            <input
              type="text"
              value={symbolsText}
              onChange={(e) => setSymbolsText(e.target.value)}
              aria-label="Symbols to remove"
              placeholder="e.g. NVDA AMD"
              className={cn(FIELD, "num w-64")}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            From date (optional)
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              aria-label="Removal start date"
              className={cn(FIELD, "num w-40")}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            To date (optional)
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              aria-label="Removal end date"
              className={cn(FIELD, "num w-40")}
            />
          </label>
          <button
            type="button"
            onClick={handlePreview}
            disabled={!hasScope || loading}
            data-testid="remove-preview-button"
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md border border-neg px-4 text-sm font-semibold text-neg",
              "transition hover:bg-surface-2 active:brightness-95",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neg focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Trash2 className="h-4 w-4" aria-hidden />}
            Preview removal
          </button>
        </div>
        <p className="text-xs text-text-faint">
          Removal deletes only user-added bars (fetched beyond the committed seed) and cascade-removes the
          snapshots and forward returns derived solely from them, leaving the dataset consistent. The
          committed seed is never deletable; a seed-only scope is refused. Nothing is fabricated — it only
          deletes.
        </p>
        {error && !preview ? (
          <p role="alert" className="flex items-center gap-2 text-sm text-neg">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
            {error}
          </p>
        ) : null}
        {done ? (
          <div
            className="flex items-start gap-2 rounded-md border border-pos bg-surface-2 p-3 text-xs text-pos"
            data-testid="remove-done"
          >
            <Database className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <span>
              Removed <span className="num">{done.removed_bar_count ?? done.removable_bar_count}</span> user-added
              bars; cascade-removed <span className="num">{done.cascade.snapshot_count}</span> snapshots and{" "}
              <span className="num">{done.cascade.forward_return_count}</span> forward returns. The coverage
              table and as-of switcher now reflect the smaller dataset.
            </span>
          </div>
        ) : null}
      </div>

      {preview ? (
        <RemoveConfirmModal
          preview={preview}
          removing={removing}
          error={error}
          onCancel={() => {
            setPreview(null);
            setError(null);
          }}
          onConfirm={handleConfirm}
        />
      ) : null}
    </Card>
  );
}

/** The J-39 confirm-preview "dialog" — an in-page modal (Card + a fixed overlay; there is no Dialog
 *  primitive in this project). It enumerates the removable bars + range, the not-removable committed-seed
 *  breakdown with reason, and the cascade of dependent snapshot/forward-return rows BEFORE any deletion.
 *  A refused (wholly-seed) scope disables the destructive confirm and shows the explicit reason. */
function RemoveConfirmModal({
  preview,
  removing,
  error,
  onCancel,
  onConfirm,
}: {
  preview: RemovePreview;
  removing: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const refused = preview.refused;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(10,14,20,0.8)] p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Confirm data removal"
      data-testid="remove-confirm-modal"
    >
      <Card className="w-full max-w-lg p-0 shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-neg">
            <AlertTriangle className="h-4 w-4" aria-hidden />
            Confirm data removal
          </h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancel"
            className="rounded p-1 text-text-faint transition hover:bg-surface-2 hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div className="space-y-3 p-4 text-sm">
          {refused ? (
            <div
              className="flex items-start gap-2 rounded-md border border-warn bg-surface-2 p-3 text-xs text-warn"
              data-testid="remove-refused"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              <span>{preview.reason}</span>
            </div>
          ) : (
            <div className="rounded-md border border-neg bg-surface-2 p-3" data-testid="remove-removable">
              <p className="text-xs uppercase tracking-wide text-text-faint">Will be removed (user-added)</p>
              <p className="num mt-1 text-lg font-semibold text-neg">
                {preview.removable_bar_count} bars
              </p>
              <p className="num text-xs text-text-muted">
                {preview.removable_symbol_count} symbol{preview.removable_symbol_count === 1 ? "" : "s"}
                {preview.removable_first ? ` · ${preview.removable_first} → ${preview.removable_last}` : null}
              </p>
              {preview.removable_symbols.length > 0 ? (
                <p className="num mt-1 truncate text-xs text-text-faint" title={preview.removable_symbols.join(", ")}>
                  {preview.removable_symbols.join(", ")}
                </p>
              ) : null}
            </div>
          )}

          {preview.not_removable_bar_count > 0 ? (
            <div className="rounded-md border border-border bg-surface-2 p-3" data-testid="remove-not-removable">
              <p className="text-xs uppercase tracking-wide text-text-faint">
                Not removable — committed seed (protected)
              </p>
              <p className="num mt-1 text-sm text-text-muted">
                {preview.not_removable_bar_count} bars kept
              </p>
              <ul className="mt-1 space-y-0.5 text-xs text-text-muted">
                {preview.not_removable_by_symbol.map((line) => (
                  <li key={line.symbol} className="flex items-baseline justify-between gap-3">
                    <span className="num font-medium text-text">{line.symbol}</span>
                    <span className="num text-text-faint">
                      {line.bar_count} bars · {line.reason}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {!refused ? (
            <div className="rounded-md border border-border bg-surface-2 p-3" data-testid="remove-cascade">
              <p className="text-xs uppercase tracking-wide text-text-faint">
                Cascade — dependent rows removed with the bars
              </p>
              <p className="num mt-1 text-sm text-text-muted">
                {preview.cascade.snapshot_count} snapshot{preview.cascade.snapshot_count === 1 ? "" : "s"} ·{" "}
                {preview.cascade.forward_return_count} forward returns
              </p>
              {preview.cascade.snapshot_dates.length > 0 ? (
                <p className="num mt-1 truncate text-xs text-text-faint" title={preview.cascade.snapshot_dates.join(", ")}>
                  dates: {preview.cascade.snapshot_dates.join(", ")}
                </p>
              ) : (
                <p className="mt-1 text-xs text-text-faint">No dependent snapshots — only bars are removed.</p>
              )}
              <p className="mt-2 text-xs text-text-faint">
                Snapshots are removed whole-row (never overwritten in place); a snapshot still holding all its
                bars is left untouched.
              </p>
            </div>
          ) : null}

          {error ? (
            <p role="alert" className="flex items-center gap-2 text-xs text-neg">
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
              {error}
            </p>
          ) : null}
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex h-9 items-center rounded-md border border-border px-4 text-sm text-text-muted transition hover:border-border-strong hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={refused || removing}
            data-testid="remove-confirm-button"
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md bg-neg px-4 text-sm font-semibold text-bg",
              "transition hover:brightness-110 active:brightness-95",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neg focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            {removing ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Trash2 className="h-4 w-4" aria-hidden />}
            {refused ? "Cannot remove" : `Remove ${preview.removable_bar_count} bars`}
          </button>
        </div>
      </Card>
    </div>
  );
}

function RunHistoryPanel({ runs }: { runs: DataRun[] }) {
  if (runs.length === 0) {
    return (
      <EmptyState
        icon={Database}
        title="No fetch / backfill runs yet"
        description="Start a job above. Each fetch or backfill run is recorded here with its date range, kind, status, and symbol/snapshot counts."
      />
    );
  }
  return (
    <Card className="overflow-x-auto p-0">
      <PanelTitle>Run history</PanelTitle>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
            <th className="px-3 py-2 font-medium">Started</th>
            <th className="px-3 py-2 font-medium">Kind</th>
            <th className="px-3 py-2 font-medium">Range</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 text-right font-medium">Symbols ok/failed</th>
            <th className="px-3 py-2 text-right font-medium">Snapshots</th>
            <th className="px-3 py-2 font-medium">Summary</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-b border-border align-top last:border-b-0 hover:bg-surface-2">
              <td className="num px-3 py-2 text-xs text-text-muted">
                {run.started_at ? run.started_at.slice(0, 19).replace("T", " ") : "—"}
              </td>
              <td className="px-3 py-2">
                <Badge variant="default">{run.kind ?? "seed load"}</Badge>
              </td>
              <td className="num px-3 py-2 text-xs text-text-muted">
                {run.start && run.end ? `${run.start} → ${run.end}` : "—"}
              </td>
              <td className="px-3 py-2">
                <Badge variant={statusVariant(run.status)} className="num">
                  {run.status}
                </Badge>
              </td>
              <td className="num px-3 py-2 text-right">
                <span className="text-pos">{run.symbols_ok}</span>
                <span className="text-text-faint"> / </span>
                <span className={run.symbols_failed > 0 ? "text-neg" : "text-text-muted"}>{run.symbols_failed}</span>
              </td>
              <td className="num px-3 py-2 text-right text-text-muted">
                {run.snapshots_created ?? "—"}
              </td>
              <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
                <span className="line-clamp-2" title={run.message ?? ""}>
                  {run.message ?? "—"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function DataSkeleton() {
  return (
    <div className="space-y-4">
      <Card className="space-y-2 p-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
        ))}
      </Card>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i} className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((__, j) => (
              <div key={j} className="h-7 w-full animate-pulse rounded bg-surface-2" />
            ))}
          </Card>
        ))}
      </div>
    </div>
  );
}
