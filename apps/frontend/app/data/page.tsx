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
import { AvailabilityHeatmap } from "@/components/availability-heatmap";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { TermInfo } from "@/components/ui/term-info";
import { cn } from "@/lib/utils";
import { formatIsoDate, formatIsoDateTime, isValidIsoDate, ISO_DATE_PLACEHOLDER } from "@/lib/dates";
import {
  dismissUnfinishedImport,
  executeDataRemoval,
  fetchDataAvailability,
  fetchDataCoverage,
  fetchDataJob,
  previewDataRemoval,
  pullMissingData,
  resumeDataJob,
  retryDataJob,
  startDataJob,
  type AvailabilityResponse,
  type DataJob,
  type DataJobKind,
  type DataOverviewResponse,
  type DataRun,
  type MissingDataDiagnostic,
  type PerSymbolCoverage,
  type ProviderSource,
  type RemovePreview,
  type RemoveScope,
  type UnfinishedImport,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: DataOverviewResponse }
  | { kind: "error" };

/** The per-trading-date availability heatmap (J-61) fetch state — independent of the coverage overview
 *  so the heatmap can show its own loading/error without blocking the rest of the page. */
type AvailabilityState =
  | { kind: "loading" }
  | { kind: "ok"; data: AvailabilityResponse }
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
    case "failed_backfill": // J-59: resumable from the backfill stage (amber, distinct from a hard red fail)
      return "warn";
    case "failed":
      return "danger";
    case "running":
      return "accent";
    case "interrupted": // J-60: an orphaned-then-swept job — a muted neutral (distinct from `failed` red)
      return "default";
    default:
      return "default";
  }
}

/** A friendlier label for the dense status badges where the raw token reads awkwardly. */
function statusLabel(status: string): string {
  if (status === "failed_backfill") return "failed at backfill";
  return status;
}

// One date authority for the whole frontend: route through the shared `formatIsoDate` (lib/dates.ts)
// so this module holds no per-component date-format literal (J-42). Kept as a thin local alias so the
// existing coverage/range/run-table call sites read clearly.
const fmtDate = formatIsoDate;

/** J-53: human-readable seconds for the per-stage job timings. Pure DISPLAY formatting of a number the
 *  backend already computed (the frontend derives no figure beyond rounding for display): sub-second →
 *  milliseconds, otherwise seconds with one decimal, rolling into "Xm Ys" past a minute. */
function fmtDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "—";
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

/** J-66: a plain-language "updated Ns ago" heartbeat string from the job's `last_progress_at`. Pure
 *  DISPLAY formatting (no derived figure beyond elapsed-since). Returns null when there is no timestamp.
 *  `nowMs` is injectable for testing / a ticking clock. */
function heartbeatAgo(lastProgressAt: string | null | undefined, nowMs: number): string | null {
  if (!lastProgressAt) return null;
  const then = Date.parse(lastProgressAt);
  if (!Number.isFinite(then)) return null;
  const secs = Math.max(0, Math.round((nowMs - then) / 1000));
  if (secs < 1) return "updated just now";
  if (secs < 60) return `updated ${secs}s ago`;
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `updated ${m}m ${s}s ago`;
}

/**
 * J-42: a locale-proof, validated ISO `yyyy-MM-dd` TEXT input for the `/data` job/removal forms — the
 * replacement for the four native `<input type="date">` pickers (whose rendered widget output is
 * locale-dependent). The user types the date directly; the value is validated against the SHARED
 * `isValidIsoDate` (exact `yyyy-MM-dd` format + calendar validity, so `2026-13-40` and `10/06/2026`
 * are both rejected). A non-empty invalid value shows a visible inline error and is reported up via
 * `onValidityChange` so the form's submit/preview button can be blocked while invalid. The submitted
 * job uses exactly the typed string. These inputs are JOB PARAMETERS — they never touch the global
 * as-of control (no `?asof` write here).
 */
function IsoDateInput({
  label,
  value,
  onChange,
  onValidityChange,
  ariaLabel,
  optional = false,
  testId,
}: {
  label: React.ReactNode;
  value: string;
  onChange: (v: string) => void;
  onValidityChange?: (valid: boolean) => void;
  ariaLabel: string;
  optional?: boolean;
  testId?: string;
}) {
  // Empty is "valid" for an optional field (no constraint); for a required field empty is incomplete
  // (not shown as an error, but reported invalid so the form blocks until both ends are filled).
  const isEmpty = value.trim() === "";
  const formatValid = isEmpty ? optional : isValidIsoDate(value);
  // Only SHOW the inline error once the user has typed something that isn't a valid ISO date — never
  // nag an untouched empty field.
  const showError = !isEmpty && !isValidIsoDate(value);
  const errorId = testId ? `${testId}-error` : undefined;

  useEffect(() => {
    onValidityChange?.(formatValid);
  }, [formatValid, onValidityChange]);

  return (
    <label className="flex flex-col gap-1 text-xs text-text-muted">
      {label}
      <input
        type="text"
        inputMode="numeric"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={ariaLabel}
        aria-invalid={showError || undefined}
        aria-describedby={showError ? errorId : undefined}
        placeholder={ISO_DATE_PLACEHOLDER}
        data-testid={testId}
        className={cn(FIELD, "num w-40", showError && "border-neg focus-visible:ring-neg")}
      />
      {showError ? (
        <span id={errorId} role="alert" className="flex items-center gap-1 text-[11px] text-neg" data-testid={errorId}>
          <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden />
          Enter a valid date as {ISO_DATE_PLACEHOLDER}
        </span>
      ) : null}
    </label>
  );
}

export default function DataManagerPage() {
  const { refresh } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [availability, setAvailability] = useState<AvailabilityState>({ kind: "loading" });
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
  // J-66: the live-job-card poll interval + the "updated Ns ago" heartbeat-stale threshold come from
  // CONFIG (No magic numbers), served on the overview payload — never a hardcoded literal. Fall back to a
  // safe default only before the first overview load resolves.
  const pollIntervalMs =
    state.kind === "ok" ? Math.max(state.data.job_progress.poll_interval_seconds, 0.1) * 1000 : 1000;
  const heartbeatStaleSeconds =
    state.kind === "ok" ? state.data.job_progress.heartbeat_stale_seconds : 20;
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

  // J-61: the per-trading-date availability heatmap reads its OWN endpoint (a read-only derivation over the
  // SAME stored bars + runs the coverage figures use). It loads on mount and re-reads after any job
  // completes / a removal (the same reload path as coverage) so the new coverage shows. On a fetch error it
  // shows no fabricated cells (mirrors the page's coverage "Backend unavailable" treatment).
  const loadAvailability = useCallback((signal?: AbortSignal) => {
    fetchDataAvailability(signal)
      .then((data) => setAvailability({ kind: "ok", data }))
      .catch(() => {
        if (!signal?.aborted) setAvailability({ kind: "error" });
      });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadOverview(controller.signal);
    loadAvailability(controller.signal);
    return () => controller.abort();
  }, [loadOverview, loadAvailability]);

  // J-61: clicking a heatmap day (start == end) or shift-click range prefills the JOB FORM's Start/End —
  // these are JOB PARAMETERS, never the global as-of control (no setAsOf call here). Marking the range as
  // user-chosen also stops the one-time gap prefill from overwriting it.
  const handleHeatmapPrefill = useCallback((s: string, e: string) => {
    prefilled.current = true;
    setStart(s);
    setEnd(e);
  }, []);

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
            loadAvailability(); // J-61: re-read the heatmap so the new coverage shows after the job
          }
        })
        .catch(() => {
          /* transient poll error — keep polling; a persistent failure surfaces in the job card */
        });
    }, pollIntervalMs); // J-66: the poll cadence comes from config (No magic numbers)
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [jobId, jobStatus, refresh, loadOverview, loadAvailability, pollIntervalMs]);

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

  // J-37 pull-missing: start a gap-exact fetch over EXACTLY the diagnosed (symbols, [start,end]) shortfall
  // and surface it in the SAME live job card (reuses the poll/refresh path). The chosen import source (and,
  // for a needs-key source, the session-only pasted key) ride along; the key never outlives the request.
  const handlePull = useCallback(
    async (symbols: string[], pullStart: string, pullEnd: string) => {
      const opts = {
        source: source || undefined,
        api_key: keyFieldVisible ? apiKey || undefined : undefined,
      };
      const resp = await pullMissingData(symbols, pullStart, pullEnd, opts);
      const snap = await fetchDataJob(resp.job_id);
      setJob(snap);
    },
    [source, apiKey, keyFieldVisible],
  );

  // J-38 retry/dismiss: after a Retry (new job) or a Remove/Dismiss, reload coverage + the unfinished
  // list. A Retry also surfaces its new job in the live card via onResumed (status running → polled).
  const onUnfinishedChanged = useCallback(() => {
    refresh();
    loadOverview();
    loadAvailability(); // J-61: a retry/dismiss may change stored coverage — re-read the heatmap too
  }, [refresh, loadOverview, loadAvailability]);

  async function handleStart(event: React.FormEvent) {
    event.preventDefault();
    if (!start || !end || starting || jobRunning) return;
    // J-42 guard: block submit (incl. via Enter) unless BOTH dates are exact, calendar-valid ISO
    // `yyyy-MM-dd` — never POST a malformed date. The Start button is also disabled while invalid.
    if (!isValidIsoDate(start) || !isValidIsoDate(end)) {
      setFormError("Enter both dates as yyyy-MM-dd (e.g. 2026-05-01).");
      return;
    }
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
          {/* J-61: the per-trading-date availability heatmap, near the coverage panel. It reads its own
              endpoint + manages its own loading/error/empty; clicking a day prefills the JOB FORM dates
              (job parameters — never the global as-of control). */}
          <AvailabilityHeatmap
            state={availability}
            selectedStart={start}
            selectedEnd={end}
            onPrefillRange={handleHeatmapPrefill}
          />
          <MissingDataDiagnosticPanel
            diagnostic={state.data.coverage.diagnostic}
            onPull={handlePull}
            pullDisabled={Boolean(jobRunning)}
          />
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
            <JobProgressPanel
              job={job}
              sources={sources}
              onResumed={onResumed}
              heartbeatStaleSeconds={heartbeatStaleSeconds}
            />
          </div>
          <UnfinishedImportsPanel
            imports={state.data.unfinished_imports}
            sources={sources}
            onResumed={onResumed}
            onChanged={onUnfinishedChanged}
            selectedSource={source}
            apiKey={keyFieldVisible ? apiKey : ""}
          />
          <RemoveDataPanel
            onRemoved={() => {
              refresh(); // the removed dates drop out of the global as-of switcher
              loadOverview(); // re-read coverage + the per-symbol table (now smaller)
              loadAvailability(); // J-61: re-read the heatmap (the removed days drop coverage)
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
  term,
}: {
  label: string;
  value: React.ReactNode;
  definition: string;
  testId?: string;
  tone?: string;
  term?: string;
}) {
  return (
    <div className="space-y-1 rounded-md border border-border bg-surface-2 p-3">
      <p className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-text-faint">
        {label}
        {term ? <TermInfo term={term} /> : null}
      </p>
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
          term="universe"
          testId="universe-count-defined"
          value={<span data-testid="universe-count">{c.universe_count}</span>}
          definition="The config-screened, SCORED names (the liquidity/price/market-cap screen result). This is the universe — distinct from symbols below."
        />
        <DefinedMetric
          label="Symbols"
          term="symbols"
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

/** J-37 Missing-data diagnostic panel (additive, alongside the J-36 Coverage panel): the three honest
 *  categories of universe members insufficient for analysis — no-history, thin, and intra-series gap —
 *  each row stating the symbol + category + EXACT shortfall, read verbatim from the GET /api/data coverage
 *  `diagnostic` field (the page re-formats backend values; it computes no shortfall). A per-row "Pull the
 *  missing data" button (on pullable rows) and a "Pull all missing" button start a gap-exact fetch over
 *  EXACTLY the diagnosed (symbols, [start,end]) shortfall via the EXISTING job-start path; on completion
 *  the diagnostic re-reads (the row clears/shrinks) and the J-36 coverage table reflects the new bars. A
 *  fine member appears in no category — an empty diagnostic renders a clean empty-state (no spurious pull). */
function MissingDataDiagnosticPanel({
  diagnostic,
  onPull,
  pullDisabled,
}: {
  diagnostic: MissingDataDiagnostic;
  onPull: (symbols: string[], start: string, end: string) => Promise<void>;
  pullDisabled: boolean;
}) {
  const { no_history, thin, intra_series_gaps, threshold, affected_count } = diagnostic;
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // "Pull all missing" — the union of every PULLABLE shortfall: each no-history member over its full
  // calendar span, plus each intra-series-gap member over its gap span. Per shortfall (symbol + its own
  // [start,end]) so each pull is gap-exact; we dispatch them sequentially (each idempotent).
  const pullableShortfalls = useMemo(() => {
    const out: { key: string; symbols: string[]; start: string; end: string; label: string }[] = [];
    for (const r of no_history) {
      if (r.pullable && r.pull_start && r.pull_end) {
        out.push({ key: `nh:${r.symbol}`, symbols: [r.symbol], start: r.pull_start, end: r.pull_end, label: r.symbol });
      }
    }
    for (const r of intra_series_gaps) {
      if (r.pullable) {
        out.push({ key: `gap:${r.symbol}`, symbols: [r.symbol], start: r.pull_start, end: r.pull_end, label: r.symbol });
      }
    }
    return out;
  }, [no_history, intra_series_gaps]);

  async function runPull(key: string, symbols: string[], start: string, end: string) {
    if (busyKey) return;
    setBusyKey(key);
    setError(null);
    try {
      await onPull(symbols, start, end);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the pull.");
    } finally {
      setBusyKey(null);
    }
  }

  async function pullAll() {
    if (busyKey || pullableShortfalls.length === 0) return;
    setBusyKey("all");
    setError(null);
    try {
      for (const s of pullableShortfalls) {
        await onPull(s.symbols, s.start, s.end);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the pull.");
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <Card className="p-0" data-testid="missing-data-diagnostic">
      <PanelTitle hint="Universe members that are insufficient for analysis, derived read-only from stored bars + the config history threshold + the benchmark trading calendar. It recomputes no score/return/bucket and fabricates nothing — a member with no/thin history or an internal gap is shown honestly. 'Pull the missing data' fetches EXACTLY the gap through the same chunked/resumable import.">
        Missing-data diagnostic
      </PanelTitle>

      {affected_count === 0 ? (
        <div className="p-4">
          <EmptyState
            title="No missing data"
            description={`Every universe member has at least ${threshold} bars (the config history threshold) and no internal gaps — nothing is insufficient for analysis.`}
          />
        </div>
      ) : (
        <>
          <p className="border-b border-border px-4 py-2 text-xs text-text-muted">
            A member needs at least{" "}
            <span className="num text-text">{threshold}</span> bars (config{" "}
            <span className="font-mono text-text-faint">indicators.min_history_bars</span>) to be analyzable.
            These members are <span className="text-warn">insufficient</span> — shown honestly as missing /
            thin / gapped (never fabricated). Pull fetches exactly the gap.
          </p>
          {pullableShortfalls.length > 0 ? (
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
              <span className="text-xs text-text-muted">
                {pullableShortfalls.length} pullable shortfall{pullableShortfalls.length === 1 ? "" : "s"}{" "}
                (no-history + intra-series gaps)
              </span>
              <button
                type="button"
                onClick={pullAll}
                disabled={Boolean(busyKey) || pullDisabled}
                data-testid="pull-all-button"
                className={cn(
                  "inline-flex h-8 items-center gap-1.5 rounded-md bg-accent px-3 text-xs font-semibold text-bg",
                  "transition hover:brightness-110 active:brightness-95",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
              >
                {busyKey === "all" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                ) : (
                  <Play className="h-3.5 w-3.5" aria-hidden />
                )}
                Pull all missing
              </button>
            </div>
          ) : null}

          <div className="divide-y divide-border">
            <DiagnosticCategory
              title="No history"
              tone="text-neg"
              hint="A universe member with ZERO stored bars."
              rows={no_history.map((r) => ({
                key: `nh:${r.symbol}`,
                symbol: r.symbol,
                shortfall: `${r.bars_have} / ${r.bars_needed} bars`,
                pullable: r.pullable,
                pullStart: r.pull_start,
                pullEnd: r.pull_end,
              }))}
              busyKey={busyKey}
              pullDisabled={pullDisabled}
              onPull={runPull}
            />
            <DiagnosticCategory
              title="Thin history"
              tone="text-warn"
              hint="0 < bars < the config threshold — too little history to analyze."
              rows={thin.map((r) => ({
                key: `thin:${r.symbol}`,
                symbol: r.symbol,
                shortfall: `${r.bars_have} / ${r.bars_needed} bars`,
                pullable: r.pullable,
                pullStart: null,
                pullEnd: null,
              }))}
              busyKey={busyKey}
              pullDisabled={pullDisabled}
              onPull={runPull}
            />
            <DiagnosticCategory
              title="Intra-series gaps"
              tone="text-warn"
              hint="Trading days (benchmark calendar) MISSING inside the member's own first→last range."
              rows={intra_series_gaps.map((r) => ({
                key: `gap:${r.symbol}`,
                symbol: r.symbol,
                shortfall: `${r.missing_day_count} missing (${fmtDate(r.first_gap)} → ${fmtDate(r.last_gap)})`,
                pullable: r.pullable,
                pullStart: r.pull_start,
                pullEnd: r.pull_end,
              }))}
              busyKey={busyKey}
              pullDisabled={pullDisabled}
              onPull={runPull}
            />
          </div>
          {error ? (
            <p role="alert" className="border-t border-border px-4 py-2 text-xs text-neg">
              {error}
            </p>
          ) : null}
        </>
      )}
    </Card>
  );
}

type DiagnosticRow = {
  key: string;
  symbol: string;
  shortfall: string;
  pullable: boolean;
  pullStart: string | null;
  pullEnd: string | null;
};

/** One diagnostic category section (no-history / thin / intra-series gap). Each row states the symbol +
 *  the EXACT shortfall and, when pullable, a "Pull the missing data" button over exactly that gap. An
 *  empty category is hidden (a fine member appears in no category). */
function DiagnosticCategory({
  title,
  tone,
  hint,
  rows,
  busyKey,
  pullDisabled,
  onPull,
}: {
  title: string;
  tone: string;
  hint: string;
  rows: DiagnosticRow[];
  busyKey: string | null;
  pullDisabled: boolean;
  onPull: (key: string, symbols: string[], start: string, end: string) => void;
}) {
  if (rows.length === 0) return null;
  return (
    <div className="p-4" data-testid={`diagnostic-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="mb-2 flex items-center gap-2">
        <span className={cn("text-sm font-semibold", tone)}>{title}</span>
        <Badge variant="default" className="num">
          {rows.length}
        </Badge>
        <span className="text-xs text-text-faint">{hint}</span>
      </div>
      <ul className="divide-y divide-border rounded-md border border-border">
        {rows.map((r) => (
          <li key={r.key} className="flex flex-wrap items-center justify-between gap-3 px-3 py-2">
            <div className="flex flex-wrap items-baseline gap-3">
              <span className="num text-sm font-medium text-text">{r.symbol}</span>
              <span className="num text-xs text-text-muted">{r.shortfall}</span>
            </div>
            {r.pullable && r.pullStart && r.pullEnd ? (
              <button
                type="button"
                onClick={() => onPull(r.key, [r.symbol], r.pullStart!, r.pullEnd!)}
                disabled={Boolean(busyKey) || pullDisabled}
                data-testid="pull-row-button"
                className={cn(
                  "inline-flex h-7 items-center gap-1.5 rounded-md border border-accent px-2.5 text-xs font-medium text-accent",
                  "transition hover:bg-accent hover:text-bg active:brightness-95",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
              >
                {busyKey === r.key ? (
                  <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                ) : (
                  <Play className="h-3 w-3" aria-hidden />
                )}
                Pull the missing data
              </button>
            ) : (
              <span className="text-xs text-text-faint">transparency only — no actionable gap</span>
            )}
          </li>
        ))}
      </ul>
    </div>
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
              <th className="px-3 py-2 font-medium">
                <span className="inline-flex items-center gap-1">In universe<TermInfo term="in-universe" /></span>
              </th>
              <th className="px-3 py-2 font-medium">Has data</th>
              <th className="px-3 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Date range<TermInfo term="date range" /></span>
              </th>
              <th className="px-3 py-2 text-right font-medium">
                <span className="inline-flex items-center justify-end gap-1">
                  <SortHeader label="Bars" active={sortKey === "bar_count"} dir={sortDir} onClick={() => toggleSort("bar_count")} right />
                  <TermInfo term="bar count" />
                </span>
              </th>
              <th className="px-3 py-2 font-medium">
                <span className="inline-flex items-center gap-1">Flag<TermInfo term="thin/missing" /></span>
              </th>
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
  // J-42: the two date fields are validated ISO TEXT inputs; the form is blocked until BOTH are a valid
  // `yyyy-MM-dd`. Memoised callbacks keep IsoDateInput's validity effect stable (one report per change).
  const [startValid, setStartValid] = useState(false);
  const [endValid, setEndValid] = useState(false);
  const onStartValid = useCallback((v: boolean) => setStartValid(v), []);
  const onEndValid = useCallback((v: boolean) => setEndValid(v), []);
  // Start is blocked while busy/running, with an empty/INVALID date, OR (J-35) when an expand is aimed at
  // a source that cannot supply market cap — the backend rejects that too; the UI blocks it up front.
  const disabled = busy || running || !start || !end || !startValid || !endValid || sourceIneligibleForExpand;
  return (
    <Card className="p-0">
      <PanelTitle hint="Pick a date or range (typed as yyyy-MM-dd), a job kind, and — for a fetch or expand — an import source. These date inputs are job parameters — they do NOT change the global as-of viewing date.">
        Start a fetch / backfill / expand job
      </PanelTitle>
      <form onSubmit={onStart} className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <IsoDateInput
            label="Start date"
            value={start}
            onChange={setStart}
            onValidityChange={onStartValid}
            ariaLabel="Job start date"
            testId="job-start-date"
          />
          <IsoDateInput
            label="End date"
            value={end}
            onChange={setEnd}
            onValidityChange={onEndValid}
            ariaLabel="Job end date"
            testId="job-end-date"
          />
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

/** J-53: the per-stage operational timings block on the job card — fetch vs backfill, each with elapsed
 *  wall-clock, items processed (symbols / dates), and the concurrency used; the backfill stage also
 *  shows the per-date-sum vs wall-clock so the ≥~2× speedup is readable. This is PURE re-formatting of
 *  `job.stages` (the backend computed every figure; this renders no derived value beyond display
 *  formatting). A stage that never ran is ABSENT from `job.stages`, so it simply does not render (NA
 *  honesty — no fabricated zero). New stat labels carry J-47 `TermInfo` tooltips reading the
 *  config-backed glossary; each tooltip trigger is a SIBLING of the label text, never nested in a
 *  clickable affordance (iter-5 lesson). */
function StageTimings({ job }: { job: DataJob }) {
  const stages = job.stages ?? {};
  const fetchStage = stages.fetch;
  const backfillStage = stages.backfill;
  if (!fetchStage && !backfillStage) return null; // no executed stage yet → nothing honest to show

  // J-66: the speedup figure is computed SERVER-SIDE and carried in the stages payload — the frontend
  // only re-formats it (no client-side division). null = honest NA (a missing/zero figure).
  const speedup = backfillStage?.speedup_factor ?? null;

  return (
    <div className="space-y-2 rounded-md border border-border bg-surface-2 p-3" data-testid="stage-timings">
      <p className="flex items-center gap-1 text-xs font-medium text-text-muted">
        <span>Stage timings</span>
        <TermInfo term="stage timings" />
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {fetchStage ? (
          <div className="space-y-1" data-testid="stage-timing-fetch">
            <p className="text-xs font-medium text-text">Fetch</p>
            <dl className="num grid grid-cols-2 gap-x-2 gap-y-0.5 text-xs text-text-muted">
              <dt>Elapsed</dt>
              <dd className="text-right text-text">{fmtDuration(fetchStage.elapsed_seconds)}</dd>
              <dt>Symbols</dt>
              <dd className="text-right text-text">{fetchStage.items_processed}</dd>
              <dt className="flex items-center gap-1">
                Concurrency
                <TermInfo term="concurrency" />
              </dt>
              <dd className="text-right text-text">{fetchStage.concurrency}×</dd>
            </dl>
          </div>
        ) : null}
        {backfillStage ? (
          <div className="space-y-1" data-testid="stage-timing-backfill">
            <p className="text-xs font-medium text-text">Backfill</p>
            <dl className="num grid grid-cols-2 gap-x-2 gap-y-0.5 text-xs text-text-muted">
              <dt>Elapsed</dt>
              <dd className="text-right text-text">{fmtDuration(backfillStage.elapsed_seconds)}</dd>
              <dt>Dates</dt>
              <dd className="text-right text-text">{backfillStage.items_processed}</dd>
              <dt className="flex items-center gap-1">
                Concurrency
                <TermInfo term="concurrency" />
              </dt>
              <dd className="text-right text-text">{backfillStage.concurrency}×</dd>
              {backfillStage.per_date_seconds_sum !== undefined ? (
                <>
                  <dt>Per-date sum</dt>
                  <dd className="text-right text-text">
                    {fmtDuration(backfillStage.per_date_seconds_sum)}
                  </dd>
                </>
              ) : null}
            </dl>
            {speedup !== null ? (
              <p className="num text-xs text-pos" data-testid="backfill-speedup">
                {speedup.toFixed(1)}× faster than the per-date sum
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

/** A 1s ticking clock (Date.now()) used ONLY while a job is live so the "updated Ns ago" heartbeat
 *  advances even between polls. Stops ticking (no interval) when the job is no longer running. */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [active]);
  return now;
}

/** J-66: the live current-activity line + "updated Ns ago" heartbeat for the job card. The activity line
 *  names what is being worked on right now (the date being scanned during backfill, the symbol/chunk
 *  during fetch — server-supplied, rendered verbatim); the heartbeat (from `last_progress_at`) ticks so a
 *  slow-but-alive job is visually distinct from a stalled one (it turns amber past the config
 *  `heartbeat_stale_seconds`). Hidden when there is nothing live to show (no activity + no heartbeat). */
function JobLiveActivity({
  job,
  heartbeatStaleSeconds,
}: {
  job: DataJob;
  heartbeatStaleSeconds: number;
}) {
  const live = job.status === "running" || job.status === "resumable";
  const now = useNow(live);
  const ago = heartbeatAgo(job.last_progress_at, now);
  const activity = job.current_activity?.trim();
  if (!activity && !ago) return null;

  // staleness: the seconds-since-last-progress vs the config threshold (amber when stale + still running).
  const then = job.last_progress_at ? Date.parse(job.last_progress_at) : NaN;
  const staleSecs = Number.isFinite(then) ? (now - then) / 1000 : 0;
  const stale = live && job.status === "running" && staleSecs > heartbeatStaleSeconds;

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-xs" data-testid="job-live-activity">
      {activity ? (
        <span className="num text-text-muted" data-testid="current-activity">
          {activity}
        </span>
      ) : (
        <span />
      )}
      {ago ? (
        <span
          className={cn("num", stale ? "text-warn" : "text-text-faint")}
          data-testid="job-heartbeat"
          title={stale ? "No progress for a while — the job may be stalled" : "The job is making progress"}
        >
          {ago}
          {stale ? " · possibly stalled" : ""}
        </span>
      ) : null}
    </div>
  );
}

function JobProgressPanel({
  job,
  sources,
  onResumed,
  heartbeatStaleSeconds,
}: {
  job: DataJob | null;
  sources: ProviderSource[];
  onResumed: (importId: string) => void;
  heartbeatStaleSeconds: number;
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
        hint={`${job.kind} job · ${job.source ? `${job.source} · ` : ""}${fmtDate(job.start)} → ${fmtDate(job.end)}`}
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

        {/* J-66: the current-activity line ("scanning 2021-03-11 (12/22)" / the symbol being fetched) +
            the "updated Ns ago" heartbeat — so a slow-but-alive job is visually distinct from a stalled
            one. Rendered only while there is something live to show (a running/resumable job). */}
        <JobLiveActivity job={job} heartbeatStaleSeconds={heartbeatStaleSeconds} />

        {/* J-67: per-date failure detail on a `partial` job — which dates failed (honest error), while the
            rest are reported complete. Never a fabricated snapshot for a failed date. */}
        {job.date_failures && job.date_failures.length > 0 ? (
          <div className="rounded-md border border-warn bg-surface-2 p-3" data-testid="date-failures">
            <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-warn">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
              {job.date_failures.length} date{job.date_failures.length === 1 ? "" : "s"} failed (the rest
              completed — no snapshot was fabricated for a failed date)
            </p>
            <ul className="max-h-40 space-y-0.5 overflow-y-auto text-xs">
              {job.date_failures.map((f, i) => (
                <li key={`${f.date}-${i}`} className="flex items-baseline justify-between gap-3">
                  <span className="num font-medium text-text">{fmtDate(f.date)}</span>
                  <span className="num truncate text-right text-warn" title={f.error}>
                    {f.error}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

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
              <span className="num" data-testid="symbols-counter">
                {/* J-66: the symbols figure counts DISTINCT symbols and never exceeds its total (the
                    `318/159` defect is gone). Defensively clamp the DISPLAY too so a stale/odd payload can
                    never render a value above the total. */}
                {Math.min(job.symbols_ok + job.symbols_failed, job.symbols_total)}/{job.symbols_total}{" "}
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

        <StageTimings job={job} />

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
      // onResumed (success ONLY) just re-reads the resumed job into the live card — it does NOT reload the
      // unfinished list, so a SUCCESSFUL resume keeps the row visible until the next overview refresh.
      onResumed(importId);
    } catch (err) {
      // J-38 / iter-25 UT-11 fix: a FAILED resume (e.g. a needs-key source resumed without a key → 400)
      // surfaces a VISIBLE inline error and does NOT call onResumed / any overview reload — so the row
      // STAYS in the Unfinished-imports panel (it is never silently dropped on a failed resume). For the
      // needs-key-without-key case we render an actionable, source-specific prompt instead of the raw 400.
      const fallback =
        needsKey && !apiKey
          ? `Enter the session key for ${source?.label ?? "this source"} to resume.`
          : "Could not resume the import.";
      setError(err instanceof Error ? err.message : fallback);
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
          <span role="alert" data-testid="resume-error" className="text-xs text-neg">
            {error}
          </span>
        ) : null}
      </div>
    </div>
  );
}

/** J-38 unified Unfinished-imports surface (generalizes the old Resumable-imports panel): EVERY import
 *  that did not finish cleanly from GET /api/data — paused/resumable durable checkpoints (Resume / Remove)
 *  AND partial/failed operational runs (Retry / Dismiss) — each with a server-built plain-language `state`
 *  rendered verbatim, done/remaining/failed counts, and chunk progress where applicable. A checkpoint row
 *  offers Resume (continues from the next chunk) + Remove (deletes the resumable checkpoint). A run row
 *  offers Retry (re-runs only outstanding/failed work, idempotent) + Dismiss (soft-dismiss — the run STAYS
 *  in Run history below). Remove/Dismiss touches NO immutable snapshot/forward-return/audit row. Hidden
 *  when there are none. */
function UnfinishedImportsPanel({
  imports,
  sources,
  onResumed,
  onChanged,
  selectedSource,
  apiKey,
}: {
  imports: UnfinishedImport[];
  sources: ProviderSource[];
  onResumed: (importId: string) => void;
  onChanged: () => void;
  selectedSource: string;
  apiKey: string;
}) {
  if (imports.length === 0) return null; // empty list hidden (no clutter when nothing is unfinished)
  return (
    <Card className="p-0" data-testid="unfinished-imports">
      <PanelTitle hint="Every import that did not finish cleanly, in one place — paused (rate-limited), partial, or failed. Resume continues a paused import from the next chunk; Retry re-runs only the outstanding/failed work (idempotent — no duplicate bar); Remove/Dismiss drops only the job-control record (the run stays in Run history below).">
        Unfinished imports
      </PanelTitle>
      <ul className="divide-y divide-border">
        {imports.map((imp) => {
          const impSource = sources.find((s) => s.id === imp.source);
          const key = `${imp.record_type}:${imp.id}`;
          return (
            <li
              key={key}
              data-testid={`unfinished-${imp.record_type}`}
              className="flex flex-wrap items-start justify-between gap-3 p-4"
            >
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={statusVariant(imp.status)} className="capitalize">
                    {statusLabel(imp.status)}
                  </Badge>
                  {imp.chunk_total ? (
                    <Badge variant="warn" className="num gap-1">
                      chunk {imp.chunk_index}/{imp.chunk_total}
                    </Badge>
                  ) : null}
                  <span className="text-sm font-medium text-text">{impSource?.label ?? imp.source}</span>
                  {imp.start && imp.end ? (
                    <span className="num text-xs text-text-faint">
                      {fmtDate(imp.start)} → {fmtDate(imp.end)}
                    </span>
                  ) : null}
                </div>
                <p className="text-xs text-text-muted" data-testid="unfinished-state">
                  {imp.state}
                </p>
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
                  {imp.bars_fetched != null ? (
                    <span className="text-text-faint"> · {imp.bars_fetched} bars so far</span>
                  ) : null}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                {imp.record_type === "checkpoint" && imp.import_id ? (
                  <ResumeControl importId={imp.import_id} source={impSource} onResumed={onResumed} />
                ) : null}
                {imp.record_type === "run" ? (
                  <RetryControl
                    runId={Number(imp.id)}
                    source={impSource}
                    selectedSource={selectedSource}
                    apiKey={apiKey}
                    onRetried={onResumed}
                    onChanged={onChanged}
                  />
                ) : null}
                <DismissControl
                  recordType={imp.record_type}
                  recordId={imp.id}
                  onDismissed={onChanged}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

/** J-38 Retry control on a partial/failed run row: re-dispatches ONLY the outstanding/failed work through
 *  the SAME chunked engine (idempotent). For a needs-key source it re-prompts for the SESSION-ONLY key
 *  (request-only — never stored/echoed; the page's current source key is offered as the default). On
 *  success the new job surfaces in the live job card (via onRetried) and the list reloads (onChanged). */
function RetryControl({
  runId,
  source,
  selectedSource,
  apiKey,
  onRetried,
  onChanged,
}: {
  runId: number;
  source: ProviderSource | undefined;
  selectedSource: string;
  apiKey: string;
  onRetried: (jobId: string) => void;
  onChanged: () => void;
}) {
  const needsKey = Boolean(source?.needs_key) && source?.available === false;
  // re-prompt for the key only when this run's source needs one and is not the page's already-keyed source
  const [localKey, setLocalKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRetry() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      // prefer the row's own re-prompted key, else the page's current session key (when same source)
      const effectiveKey = localKey || (source && source.id === selectedSource ? apiKey : "") || undefined;
      const resp = await retryDataJob(runId, needsKey ? { api_key: effectiveKey } : undefined);
      setLocalKey(""); // drop the session-only key the instant the retry is submitted
      onRetried(resp.job_id);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not retry the import.");
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
            value={localKey}
            onChange={(e) => setLocalKey(e.target.value)}
            aria-label={`Session API key to retry run ${runId}`}
            autoComplete="off"
            placeholder={source?.env_var ? `or set $${source.env_var}` : "paste a key"}
            className={cn(FIELD, "w-72")}
          />
        </label>
      ) : null}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={handleRetry}
          disabled={busy}
          data-testid="retry-button"
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
          Retry remaining
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

/** J-38 Remove/Dismiss control on every unfinished row: drops ONLY the job-control record (a resumable
 *  checkpoint is deleted; a partial/failed run is soft-dismissed). Touches NO immutable snapshot/
 *  forward-return/audit row — a dismissed run stays in Run history below. */
function DismissControl({
  recordType,
  recordId,
  onDismissed,
}: {
  recordType: "checkpoint" | "run";
  recordId: string | number;
  onDismissed: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDismiss() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await dismissUnfinishedImport(recordType, recordId);
      onDismissed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove the record.");
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <button
        type="button"
        onClick={handleDismiss}
        disabled={busy}
        data-testid="dismiss-button"
        title={
          recordType === "run"
            ? "Dismiss this run from the actionable list (it stays in Run history)"
            : "Remove this resumable checkpoint"
        }
        className={cn(
          "inline-flex h-8 items-center gap-1.5 rounded-md border border-border px-3 text-xs font-medium text-text-muted",
          "transition hover:border-border-strong hover:text-text active:brightness-95",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        {busy ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
        ) : (
          <X className="h-3.5 w-3.5" aria-hidden />
        )}
        {recordType === "run" ? "Dismiss" : "Remove"}
      </button>
      {error ? (
        <span role="alert" className="text-xs text-neg">
          {error}
        </span>
      ) : null}
    </div>
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
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [preview, setPreview] = useState<RemovePreview | null>(null);
  const [loading, setLoading] = useState(false); // preview in-flight
  const [removing, setRemoving] = useState(false); // destructive removal in-flight
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<RemovePreview | null>(null);
  // J-69: removal is scoped PURELY by date range over all symbols — there is no symbols input. BOTH date
  // fields are MANDATORY (guarding against an accidental delete-everything): each must be a non-empty,
  // valid `yyyy-MM-dd` before a preview is allowed. IsoDateInput reports a required-but-empty field as
  // invalid, so an empty end (or start) keeps the button disabled.
  const [startValid, setStartValid] = useState(false);
  const [endValid, setEndValid] = useState(false);
  const onStartValid = useCallback((v: boolean) => setStartValid(v), []);
  const onEndValid = useCallback((v: boolean) => setEndValid(v), []);

  function buildScope(): RemoveScope {
    // J-69: range-only — both dates, no symbols. The destructive flow never sends a symbols field.
    return { start, end };
  }

  // J-69: both date fields must be non-empty AND valid ISO before a preview is allowed (the range is
  // mandatory). IsoDateInput's required-empty → invalid handles the "both filled" gate.
  const datesValid = Boolean(start) && Boolean(end) && startValid && endValid;

  async function handlePreview() {
    if (loading || !datesValid) return;
    // J-42/J-69 guard: never preview/POST a malformed or single-ended date range (the button is also
    // disabled until both ends are valid ISO).
    if (!isValidIsoDate(start) || !isValidIsoDate(end)) {
      setError("Enter both dates as yyyy-MM-dd (e.g. 2026-05-01).");
      return;
    }
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
      <PanelTitle hint="Delete imported (user-added) data beyond the committed seed by date range — both From and To are required (no symbol entry). A confirm-preview shows exactly what will be removed first. These date inputs are action parameters — they do NOT change the global as-of viewing date. The committed seed is never deletable.">
        Remove imported data
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <IsoDateInput
            label="From date (required)"
            value={start}
            onChange={setStart}
            onValidityChange={onStartValid}
            ariaLabel="Removal start date"
            testId="remove-start-date"
          />
          <IsoDateInput
            label="To date (required)"
            value={end}
            onChange={setEnd}
            onValidityChange={onEndValid}
            ariaLabel="Removal end date"
            testId="remove-end-date"
          />
          <button
            type="button"
            onClick={handlePreview}
            disabled={loading || !datesValid}
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
          Removal is scoped by date range over all symbols — both From and To are required. It deletes only
          user-added bars (fetched beyond the committed seed) and cascade-removes the snapshots and forward
          returns derived solely from them, leaving the dataset consistent. The committed seed is never
          deletable; a seed-only range is refused. Nothing is fabricated — it only deletes.
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

/** The J-39/J-69 confirm-preview "dialog" — an in-page modal (Card + a fixed overlay; there is no Dialog
 *  primitive in this project). J-69 — the body is COUNTS-ONLY: the removable (user-added) bar count, the
 *  affected-symbol count, a summary protected-seed bar count, and the cascade snapshot / forward-return
 *  counts, with the date range restated — NO long enumerated symbol lists (which could push the Confirm
 *  button off-screen for a large range). The body scrolls within a capped max-height while the footer
 *  action row stays OUTSIDE that scroll region, so the Confirm button is persistently visible for any
 *  range. A refused (wholly-seed) scope disables the destructive confirm and shows the explicit reason. */
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
        {/* J-69: the body scrolls within a capped max-height so the footer (Confirm) stays visible for
            any range; it is COUNTS-ONLY — no long enumerated symbol/snapshot lists. */}
        <div className="max-h-[55vh] space-y-3 overflow-y-auto p-4 text-sm">
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
              <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1">
                <div>
                  <p className="num text-lg font-semibold text-neg" data-testid="remove-bar-count">
                    {preview.removable_bar_count}
                  </p>
                  <p className="text-xs text-text-faint">bars</p>
                </div>
                <div>
                  <p className="num text-lg font-semibold text-neg" data-testid="remove-symbol-count">
                    {preview.removable_symbol_count}
                  </p>
                  <p className="text-xs text-text-faint">
                    affected symbol{preview.removable_symbol_count === 1 ? "" : "s"}
                  </p>
                </div>
              </div>
              {preview.removable_first ? (
                <p className="num mt-2 text-xs text-text-muted" data-testid="remove-range">
                  range: {fmtDate(preview.removable_first)} → {fmtDate(preview.removable_last)}
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
            </div>
          ) : null}

          {!refused ? (
            <div className="rounded-md border border-border bg-surface-2 p-3" data-testid="remove-cascade">
              <p className="text-xs uppercase tracking-wide text-text-faint">
                Cascade — dependent rows removed with the bars
              </p>
              <p className="num mt-1 text-sm text-text-muted" data-testid="remove-cascade-counts">
                {preview.cascade.snapshot_count} snapshot{preview.cascade.snapshot_count === 1 ? "" : "s"} ·{" "}
                {preview.cascade.forward_return_count} forward returns
              </p>
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
                {formatIsoDateTime(run.started_at)}
              </td>
              <td className="px-3 py-2">
                <Badge variant="default">{run.kind ?? "seed load"}</Badge>
              </td>
              <td className="num px-3 py-2 text-xs text-text-muted">
                {run.start && run.end ? `${fmtDate(run.start)} → ${fmtDate(run.end)}` : "—"}
              </td>
              <td className="px-3 py-2">
                <Badge variant={statusVariant(run.status)} className="num" data-testid="run-status">
                  {/* J-60: running (in-flight from job start) / interrupted (orphan swept on boot) read
                      alongside the terminal ok/partial/failed states. */}
                  {run.status === "running" ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" aria-hidden />
                  ) : null}
                  {statusLabel(run.status)}
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
