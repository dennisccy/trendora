"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Database,
  GitCompare,
  History,
  KeyRound,
  Loader2,
  Play,
  RotateCcw,
  Search,
  TrendingUp,
  Trash2,
  X,
} from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { AvailabilityHeatmap } from "@/components/availability-heatmap";
import { EmptyState } from "@/components/empty-state";
import { IndexVendorPanel } from "@/components/index-vendor-panel";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { TermInfo } from "@/components/ui/term-info";
import { cn } from "@/lib/utils";
import { formatIsoDate, formatIsoDateTime, isValidIsoDate, ISO_DATE_PLACEHOLDER } from "@/lib/dates";
import {
  MEMBERSHIP_TIMELINE_PAGE_SIZE,
  ALL_SENTINEL,
  deriveYearOptions,
  deriveMonthOptions,
  filterTimelinePoints,
  paginateTimelinePoints,
} from "@/lib/membership-timeline-view";
import {
  type AbsentFromLatestSnapshot,
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
  type DataCapacity,
  type DataJob,
  type DataJobKind,
  type DataOverviewResponse,
  type DataRun,
  type DriftReport,
  type MacroAvailability,
  type MembershipTimeline,
  type MissingDataDiagnostic,
  type PerSymbolCoverage,
  type PoolSurvivorship,
  type ProviderSource,
  type RemovePreview,
  type RemoveScope,
  type UnfinishedImport,
  type UniverseDiagnostic,
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

/** ops-hardening iter-1 (J-01) — a "zero-work" outcome: a backfill/both/rebuild run that finished `ok`
 *  but created NO NEW snapshots (every in-range trading day was already snapshotted, or the range held
 *  no trading days at all). Per goal.md's explicit anti-goal language ("never the same unexplained green
 *  success badge"), this must read as visually DISTINCT from a productive success. */
function isZeroWorkRun(
  kind: string | null | undefined,
  status: string,
  snapshotsCreated: number | null | undefined,
): boolean {
  const isBackfillLike = kind === "backfill" || kind === "both" || kind === "rebuild";
  return status === "ok" && isBackfillLike && snapshotsCreated === 0;
}

/** Job/run status -> badge variant, aware of the J-01 zero-work distinction above; falls back to the
 *  existing `statusVariant` for every other case (never re-implements the ok/warn/danger/accent mapping).
 *  Mirrors the existing `interrupted` precedent: a neutral (not green) badge for a clean-but-uneventful
 *  outcome, never the same unexplained green success look. */
function runStatusVariant(
  kind: string | null | undefined,
  status: string,
  snapshotsCreated: number | null | undefined,
): "ok" | "warn" | "danger" | "accent" | "default" {
  if (isZeroWorkRun(kind, status, snapshotsCreated)) return "default";
  return statusVariant(status);
}

/** Job/run status -> badge label, aware of the J-01 zero-work distinction — factual wording, no
 *  reassurance language (goal.md's anti-goal: "zero-work is never rendered as unexplained success"). */
function runStatusLabel(
  kind: string | null | undefined,
  status: string,
  snapshotsCreated: number | null | undefined,
): string {
  if (isZeroWorkRun(kind, status, snapshotsCreated)) return "no new snapshots";
  return statusLabel(status);
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

/** Item K (iter-24): human-readable byte size for the storage-footprint card (1024-based B/KB/MB/GB/TB).
 *  Pure DISPLAY formatting of the server-provided byte count — no size is computed here. */
function fmtBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  const decimals = exponent === 0 ? 0 : value < 10 ? 2 : 1;
  return `${value.toFixed(decimals)} ${units[exponent]}`;
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
  // iter-33 (J-93/J-94): the coverage block's dynamic universe_count + per-date diagnostic are resolved
  // at the SINGLE GLOBAL as-of (the same `useAsOf` control every date-scoped page reads — NOT a second
  // date state). `asOf` (null ⇒ latest) is threaded to GET /api/data so stepping the global switcher
  // slides the resolved-universe figures. The job-form date inputs remain job PARAMETERS (unrelated).
  const { refresh, asOf } = useAsOf();
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
  // Fetch/both pull from a live import source.
  const isFetchKind = kind === "fetch" || kind === "both";
  // Reveal the session-only key field only for a needs-key source with no env key (an available source
  // already has its key in the environment — no paste needed).
  const keyFieldVisible = isFetchKind && Boolean(selectedSource?.needs_key) && selectedSource?.available === false;

  const loadOverview = useCallback((signal?: AbortSignal) => {
    fetchDataCoverage(asOf ?? undefined, signal)
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
  }, [asOf]);

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
          {/* item K (iter-24 fast-platform pass): the read-only DB storage-footprint card (file size +
              three row counts) from the additive GET /api/data `capacity` field. */}
          <StorageCapacityPanel capacity={state.data.capacity} />
          {/* iter-35 (J-21/B-304): the live-vs-seed drift report from the SAME additive `/api/data`
              payload (no new fetch) -- quiet when clean/absent, loud amber when a re-adjustment or an
              unreadable artifact is reported. The site-wide preflight banner (already generic) reflects
              the same signal via its own `drift` reason when readiness degrades. */}
          <DriftReportPanel drift={state.data.drift} />
          {/* J-85: the universe-vs-latest-snapshot coverage diagnostic banner (only when members are
              absent) + the confirm-gated "Rebuild snapshots for current universe" action. The rebuild
              POSTs kind="rebuild" and surfaces its progress through the SAME live job card / poll path
              (setJob) — no second progress surface. The rebuild ignores dates (the full covered calendar). */}
          <RebuildPanel
            absent={state.data.coverage.absent_from_latest_snapshot}
            latestDate={state.data.coverage.snapshot_dates[0] ?? state.data.coverage.price_end}
            running={Boolean(jobRunning)}
            onStarted={setJob}
          />
          {/* J-94: the per-date coverage diagnostic — the admitted count + excluded-by-reason counts at
              the current global as-of, explaining the warm-up window. Reads the single global as-of. */}
          <UniverseDiagnosticPanel
            diagnostic={state.data.coverage.universe_diagnostic}
            asof={state.data.coverage.universe_asof}
          />
          {/* J-96: the dynamic-universe membership timeline — per-snapshot-date resolved size (step
              function) + entries/exits + excluded counts + the three honest survivorship/warm-up labels. */}
          <MembershipTimelinePanel timeline={state.data.coverage.membership_timeline} />
          {/* J-95: the confirm-gated "extend history backward" control (reuses the rebuild confirm chrome
              + the live job card). The real backward-history fetch is data-walled → honest blocked-NA. */}
          <BackwardHistoryPanel
            survivorship={state.data.coverage.membership_timeline.labels.survivorship}
            priceStart={state.data.coverage.price_start}
            running={Boolean(jobRunning)}
            onStarted={setJob}
          />
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
          {/* J-92: the OPTIONAL FRED macro feed catalog — env-detected availability, per-series committed-
              seed coverage, honest blocked-NA for a walled/uncommitted series, and the per-leg
              config-default-OFF flags. Read-only descriptive metadata; never a key value. */}
          <MacroFeedPanel macro={state.data.macro} />

          {/* iter-22 (J-14): the index/benchmark/macro vendor-disclosure panel — reads the SAME
              GET /api/indexes payload the Dashboard major-indexes chart reads (an additional reader,
              not a new endpoint or a meta.json re-parse). Independent loading/error/empty state. */}
          <IndexVendorPanel />

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
              runs={state.data.runs}
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

/** J-92 — the OPTIONAL FRED macro feed catalog in the Data Manager. Surfaces the macro provider's
 *  env-detected live availability (the FRED key env-var NAME only — never the value), the per-leg
 *  config-default-OFF enable flags, and each configured series' committed-seed coverage with an honest
 *  blocked/unavailable (NA) state for a walled/uncommitted series. Read-only descriptive metadata —
 *  fabricates nothing, and (since macro is config-default-OFF) the default analysis figures are unchanged. */
function MacroFeedPanel({ macro }: { macro: MacroAvailability }) {
  const anyEnabled = macro.enable.severity || macro.enable.regime_switching || macro.enable.study;
  return (
    <Card className="p-0" data-testid="macro-feed-panel">
      <PanelTitle hint="Optional FRED macro feed — yield-curve, unemployment, and credit-spread series + their OHLCV proxies, publication-lag aligned. Config-default-OFF, so default analysis figures are unchanged. Live pulls read the FRED key from the environment only (never stored); a walled or uncommitted series is shown as NA, never fabricated.">
        <span className="inline-flex items-center gap-2">
          <Activity className="h-4 w-4 text-text-faint" aria-hidden />
          {macro.label}
        </span>
      </PanelTitle>
      <div className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-text-muted">
          <span>
            <span className="text-text-faint">Provider: </span>
            <span className="font-semibold text-text">{macro.provider}</span>
          </span>
          <span>
            <span className="text-text-faint">Live key ({macro.env_var}): </span>
            <Badge variant={macro.live_available ? "ok" : "default"} data-testid="macro-live-available">
              {macro.live_available ? "detected" : "not set (NA)"}
            </Badge>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="text-text-faint">Wired legs: </span>
            <Badge variant={macro.enable.severity ? "ok" : "default"}>severity {macro.enable.severity ? "on" : "off"}</Badge>
            <Badge variant={macro.enable.regime_switching ? "ok" : "default"}>regime {macro.enable.regime_switching ? "on" : "off"}</Badge>
            <Badge variant={macro.enable.study ? "ok" : "default"}>study {macro.enable.study ? "on" : "off"}</Badge>
          </span>
        </div>

        {!anyEnabled ? (
          <p className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted" data-testid="macro-default-off-note">
            All macro legs are off by default — the dashboard market-phase panel and the Research downtrend
            study use the price / breadth / VIX path only, so default figures are unchanged. Enable a leg in
            config to incorporate macro inputs.
          </p>
        ) : null}

        <div className="overflow-x-auto">
          <table data-testid="macro-series-table" className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">Series</th>
                <th className="px-3 py-2 font-medium">FRED id</th>
                <th className="px-3 py-2 text-right font-medium">Pub. lag (days)</th>
                <th className="px-3 py-2 font-medium">Proxy</th>
                <th className="px-3 py-2 text-right font-medium">Committed obs.</th>
                <th className="px-3 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {macro.series.map((s) => (
                <tr key={s.id} className="border-b border-border last:border-b-0" data-testid={`macro-series-${s.id}`}>
                  <td className="px-3 py-2 text-text">{s.label}</td>
                  <td className="px-3 py-2 num text-text-muted">{s.fred_series_id}</td>
                  <td className="px-3 py-2 num text-right text-text-muted">{s.publication_lag_days}</td>
                  <td className="px-3 py-2 num text-text-muted">{s.proxy_symbol ?? "—"}</td>
                  <td className="px-3 py-2 num text-right text-text">{s.committed_rows}</td>
                  <td className="px-3 py-2">
                    <Badge variant={s.available ? "ok" : "default"} title={s.reason}>
                      {s.available ? "available" : "NA"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-xs leading-snug text-text-faint">{macro.publication_lag_note}</p>
      </div>
    </Card>
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
          label="Universe (as of date)"
          term="universe"
          testId="universe-count-defined"
          value={<span data-testid="universe-count">{c.universe_count}</span>}
          definition={
            "The point-in-time SCORED universe resolved at the current as-of" +
            (c.universe_asof ? ` (${formatIsoDate(c.universe_asof)})` : "") +
            ` — names with ≥ ${c.universe_diagnostic.thresholds.min_history_bars} bars, a fresh series (last bar within ${c.universe_diagnostic.thresholds.max_staleness_days} days), price, and liquidity from bars on/before that date. Step the global as-of to slide it. Of ${c.candidate_universe_count} candidate names / ${c.candidate_pool_count} pool.`
          }
        />
        <DefinedMetric
          label="Candidate universe"
          value={<span data-testid="candidate-universe-count">{c.candidate_universe_count}</span>}
          definition="The static screened candidate universe (market-cap/ADV/price pool) the per-date resolver screens. Not date-scoped — the date-resolved subset is shown above."
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
        <span className="font-medium text-text-muted">Dynamic universe (J-93): </span>
        the <span className="text-text">universe</span> ({c.universe_count}) is now POINT-IN-TIME — the
        candidate names that clear the price / liquidity / minimum-history gate from bars on or before the
        current as-of, a subset of the {c.candidate_universe_count} candidate names. Step the global as-of
        and it slides (early dates are honestly smaller or empty during warm-up).{" "}
        <span className="text-text">symbols</span> ({c.symbol_count}) is every ticker with bars (incl. the
        ETFs and <span className="num">^VIX</span>).
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
      <PerSymbolCoverageTable rows={c.per_symbol} symbolCount={c.symbol_count} universeCount={c.candidate_universe_count} />
    </Card>
  );
}

/** Item K (iter-24 fast-platform pass) — the DB storage-footprint snapshot: on-disk file size + row
 *  counts for the three largest tables, read verbatim from the additive `GET /api/data` `capacity`
 *  field. Pure presentation of stored values (recomputes nothing); an honest zero state on a cold DB
 *  (the backend's `compute_capacity` already returns 0s there — no separate empty-state branch needed).
 *  On a backend-fetch failure this card simply doesn't render (the page's existing "Backend unavailable"
 *  error card already covers that — see the `state.kind === "error"` branch above). */
function StorageCapacityPanel({ capacity }: { capacity: DataCapacity }) {
  return (
    <Card className="p-0" data-testid="storage-capacity-panel">
      <PanelTitle hint="The database's current on-disk footprint — file size and row counts for the three largest tables. Descriptive metadata read from stored rows; it recomputes no canonical value.">
        <span className="inline-flex items-center gap-2">
          <Database className="h-4 w-4 text-text-faint" aria-hidden />
          Storage footprint
        </span>
      </PanelTitle>
      <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <DefinedMetric
          label="Database file"
          testId="capacity-db-file-bytes"
          value={fmtBytes(capacity.db_file_bytes)}
          definition="The on-disk size of the SQLite database file."
        />
        <DefinedMetric
          label="Price bars"
          testId="capacity-daily-prices-rows"
          value={capacity.daily_prices_rows.toLocaleString()}
          definition="Rows in daily_prices — one per (symbol, date) stored bar."
        />
        <DefinedMetric
          label="Scanner rows"
          testId="capacity-scanner-results-rows"
          value={capacity.scanner_results_rows.toLocaleString()}
          definition="Rows in scanner_results — one per (snapshot run, stock) scored result."
        />
        <DefinedMetric
          label="Forward returns"
          testId="capacity-forward-returns-rows"
          value={capacity.forward_returns_rows.toLocaleString()}
          definition="Rows in forward_returns — one per (snapshot run, symbol, horizon) realized return."
        />
      </div>
    </Card>
  );
}

/** iter-35 (J-21/B-304) — the live-vs-seed drift report: whether the most recent Fetch job's overlap
 *  window agreed with the committed seed. Mirrors `StorageCapacityPanel`'s Card/PanelTitle pattern.
 *  Reads the additive `drift` field from the SAME `/api/data` payload already in use (no new fetch).
 *  Quiet/neutral when no fetch has run yet or the last one was clean; LOUD (amber, matching the
 *  preflight banner's DEGRADED treatment) when a re-adjustment was detected or the artifact could not be
 *  read — descriptive integrity reporting only, never a proven/not-proven claim, never auto-repairs. */
function DriftReportPanel({ drift }: { drift: DriftReport | null | undefined }) {
  return (
    <Card className="p-0" data-testid="drift-report-panel">
      <PanelTitle hint="Byte/fixed-precision compares the last N dates a Fetch job returns against the committed seed. A mismatch means the live provider silently re-adjusted already-committed history (an adjustment seam) — descriptive integrity reporting, recomputes nothing, never auto-repairs or re-fetches.">
        <span className="inline-flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-text-faint" aria-hidden />
          Live-vs-seed drift
        </span>
      </PanelTitle>

      {!drift ? (
        <p className="p-4 text-xs text-text-muted" data-testid="drift-status-absent">
          No fetch has run yet — nothing to compare against the committed seed.
        </p>
      ) : drift.status === "clean" ? (
        <p className="flex items-center gap-2 p-4 text-xs text-pos" data-testid="drift-status-clean">
          <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden />
          The most recent fetch matched the committed seed over the last{" "}
          <span className="num">{drift.overlap_days ?? "—"}</span> common date(s).
        </p>
      ) : drift.status === "drift" ? (
        <div
          className="m-4 flex items-start gap-2 rounded-md border border-warn bg-warn/10 p-3 text-xs text-warn"
          data-testid="drift-status-drift"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <div className="space-y-2">
            <p className="font-semibold">
              Live-vs-seed drift detected — the provider re-adjusted already-committed history for{" "}
              <span className="num">{drift.affected.length}</span> symbol{drift.affected.length === 1 ? "" : "s"}.
            </p>
            <ul className="space-y-1">
              {drift.affected.map((a) => (
                <li key={a.symbol} data-testid={`drift-affected-${a.symbol}`}>
                  <span className="num font-semibold">{a.symbol}</span>
                  {": "}
                  <span className="num">{a.mismatching_dates.map((d) => fmtDate(d)).join(", ")}</span>
                  {" — "}
                  <span className="italic">adjustment seam</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div
          className="m-4 flex items-start gap-2 rounded-md border border-warn bg-warn/10 p-3 text-xs text-warn"
          data-testid="drift-status-unreadable"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <span>The drift report exists but could not be read. Re-run a Fetch job to regenerate it.</span>
        </div>
      )}
    </Card>
  );
}

/** J-85 — the universe-vs-latest-snapshot coverage diagnostic banner + the confirm-gated
 *  "Rebuild snapshots for current universe" action. The amber banner appears ONLY when members are absent
 *  from the latest snapshot (`absent.absent_count > 0`); at 0 absent it renders an honest "all members in
 *  the latest snapshot" note (no alarming banner). The rebuild is CONFIRM-GATED via the J-69 modal pattern
 *  (Card + fixed overlay; a persistently-visible Confirm button outside any scroll region). Confirming
 *  POSTs kind="rebuild" — a wholesale regenerate-from-scratch over the FULL covered calendar (dates are
 *  ignored by the rebuild) — and surfaces its progress through the SAME live job card via `onStarted`
 *  (no second progress surface; J-66). The committed price seed is never deleted by a rebuild. */
function RebuildPanel({
  absent,
  latestDate,
  running,
  onStarted,
}: {
  absent: AbsentFromLatestSnapshot;
  latestDate: string | null;
  running: boolean;
  onStarted: (job: DataJob) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasAbsent = absent.absent_count > 0;

  async function handleConfirm() {
    if (starting || running) return;
    setStarting(true);
    setError(null);
    try {
      // The rebuild IGNORES the supplied dates (the full covered calendar by design); the API still
      // requires a start/end, so pass the latest snapshot/price date as a structural placeholder for both.
      const placeholder = latestDate ?? new Date().toISOString().slice(0, 10);
      const resp = await startDataJob("rebuild", placeholder, placeholder);
      const snap = await fetchDataJob(resp.job_id); // seed the live job card
      onStarted(snap);
      setConfirming(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the rebuild.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <Card className="p-0" data-testid="rebuild-panel">
      <PanelTitle hint="Regenerate every immutable snapshot from scratch over the current resolved universe — so newly-expanded members appear in every read surface. The committed price seed is never deleted; no canonical formula changes (only the universe scanned over). Dates are not a parameter — the rebuild covers the full calendar.">
        Rebuild snapshots for current universe
      </PanelTitle>
      <div className="space-y-3 p-4 text-sm">
        {hasAbsent ? (
          <div
            className="flex items-start gap-2 rounded-md border border-warn bg-surface-2 p-3 text-xs text-warn"
            data-testid="coverage-absent-banner"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <span>
              <span className="num font-semibold">{absent.absent_count}</span> universe member
              {absent.absent_count === 1 ? "" : "s"} (of {absent.universe_count}){" "}
              {absent.absent_count === 1 ? "is" : "are"} absent from the latest snapshot
              {absent.latest_snapshot_date ? ` (${formatIsoDate(absent.latest_snapshot_date)})` : ""} —
              rebuild to include {absent.absent_count === 1 ? "it" : "them"}.
              {absent.absent_preview.length > 0 ? (
                <span className="num"> e.g. {absent.absent_preview.join(", ")}</span>
              ) : null}
            </span>
          </div>
        ) : (
          <p className="text-xs text-text-muted" data-testid="coverage-absent-none">
            All {absent.universe_count} resolved-universe members are present in the latest snapshot
            {absent.latest_snapshot_date ? ` (${formatIsoDate(absent.latest_snapshot_date)})` : ""}. A
            rebuild is optional — it deterministically regenerates the whole snapshot set from scratch.
          </p>
        )}
        <button
          type="button"
          onClick={() => setConfirming(true)}
          disabled={running || starting}
          data-testid="rebuild-button"
          className={cn(
            "inline-flex h-9 items-center gap-2 rounded-md border px-4 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            running || starting
              ? "cursor-not-allowed border-border text-text-faint"
              : "border-warn text-warn hover:bg-surface-2",
          )}
        >
          <RotateCcw className="h-4 w-4" aria-hidden />
          Rebuild snapshots for current universe
        </button>
        {running ? (
          <p className="text-xs text-text-faint">A job is already running — wait for it to finish before rebuilding.</p>
        ) : null}
      </div>
      {confirming ? (
        <RebuildConfirmModal
          absent={absent}
          starting={starting}
          error={error}
          onCancel={() => {
            setConfirming(false);
            setError(null);
          }}
          onConfirm={handleConfirm}
        />
      ) : null}
    </Card>
  );
}

/** The J-69-pattern confirm modal for the J-85 rebuild — an in-page modal (Card + fixed overlay; no Dialog
 *  primitive in this project), with a persistently-visible Confirm button OUTSIDE any scroll region. It
 *  restates what the rebuild does (a from-scratch regenerate; the price seed is never deleted) so the
 *  destructive-sounding action is never a surprise. */
function RebuildConfirmModal({
  absent,
  starting,
  error,
  onCancel,
  onConfirm,
}: {
  absent: AbsentFromLatestSnapshot;
  starting: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(10,14,20,0.8)] p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Confirm snapshot rebuild"
      data-testid="rebuild-confirm-modal"
    >
      <Card className="w-full max-w-lg p-0 shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-warn">
            <RotateCcw className="h-4 w-4" aria-hidden />
            Confirm snapshot rebuild
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
        <div className="max-h-[55vh] space-y-3 overflow-y-auto p-4 text-sm">
          <p className="text-text-muted">
            This clears the entire snapshot set and recomputes a snapshot + forward returns for EVERY
            covered trading day, over the current resolved universe ({absent.universe_count} members).
          </p>
          <ul className="list-disc space-y-1 pl-5 text-xs text-text-faint">
            <li>The committed price seed is never deleted — only the derived snapshots are regenerated.</li>
            <li>No canonical score/return formula changes — only the universe membership scanned over.</li>
            <li>It can take several minutes; progress shows in the job card below.</li>
            {absent.absent_count > 0 ? (
              <li className="text-warn">
                After it completes, the {absent.absent_count} currently-absent member
                {absent.absent_count === 1 ? "" : "s"} will appear in every read surface.
              </li>
            ) : null}
          </ul>
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
            disabled={starting}
            data-testid="rebuild-confirm-button"
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md border border-warn bg-warn/10 px-4 text-sm font-semibold text-warn transition hover:bg-warn/20 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              starting && "cursor-not-allowed opacity-60",
            )}
          >
            {starting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <RotateCcw className="h-4 w-4" aria-hidden />}
            {starting ? "Starting…" : "Rebuild snapshots"}
          </button>
        </div>
      </Card>
    </div>
  );
}

/** J-94 — the per-date coverage diagnostic. For the SINGLE GLOBAL as-of (read from the coverage payload,
 *  resolved server-side; NOT a second date state) it shows the ADMITTED member count + the excluded-by-
 *  reason counts (below history / below price / below liquidity) against the candidate-pool denominator,
 *  plus the exact config thresholds — so the small/empty warm-up window is explained, never mysterious. A
 *  resolved as-of before the warm-up boundary renders an explicit honest empty-universe state. Read-only;
 *  the page re-formats backend values (it computes no count). */
function UniverseDiagnosticPanel({
  diagnostic,
  asof,
}: {
  diagnostic: UniverseDiagnostic;
  asof: string | null;
}) {
  const t = diagnostic.thresholds;
  const empty = diagnostic.admitted_count === 0;
  const reasons: { key: string; label: string; value: number; defn: string }[] = [
    {
      key: "below_history",
      label: "Below min history",
      value: diagnostic.excluded.below_history,
      defn: `Fewer than ${t.min_history_bars} trailing bars on/before the as-of (incl. un-fetched pool names).`,
    },
    {
      // iter-18 (J-12): the recency gate — a name whose data ENDED mid-history exits membership cleanly
      // and never feeds a misaligned relative-strength window. Threshold read from the served config.
      key: "stale_series",
      label: "Stale series",
      value: diagnostic.excluded.stale_series,
      defn: `Last bar more than ${t.max_staleness_days} calendar days before the as-of — the series ended or halted, so the name exits membership (its months-old close can never misalign a relative-strength window).`,
    },
    {
      key: "below_price",
      label: "Below min price",
      value: diagnostic.excluded.below_price,
      defn: `As-of close under $${t.min_price}.`,
    },
    {
      key: "below_adv",
      label: "Below min liquidity",
      value: diagnostic.excluded.below_adv,
      defn: `${t.adv_window_days}-day average daily dollar volume under $${Number(t.min_dollar_vol).toLocaleString()}.`,
    },
  ];
  return (
    <Card className="p-0" data-testid="universe-diagnostic-panel">
      <PanelTitle
        hint={`Why the scored universe is the size it is at the current as-of${
          asof ? ` (${formatIsoDate(asof)})` : ""
        } — the point-in-time resolver admits a candidate only with ≥ ${t.min_history_bars} bars, a FRESH series (last bar within ${t.max_staleness_days} calendar days of the as-of), price ≥ $${t.min_price}, and ${t.adv_window_days}-day liquidity, all from bars on/before the date. Reads the single global as-of (no second date control).`}
      >
        <span className="inline-flex items-center gap-2">
          <Search className="h-4 w-4 text-text-faint" aria-hidden />
          Universe resolution {asof ? `as of ${formatIsoDate(asof)}` : "(latest)"}
        </span>
      </PanelTitle>
      <div className="space-y-3 p-4">
        {empty ? (
          <div
            className="flex items-start gap-2 rounded-md border border-warn bg-surface-2 p-3 text-xs text-warn"
            data-testid="universe-diagnostic-empty"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <span>
              No candidate clears the screen at this date — the resolved universe is honestly EMPTY (a
              warm-up date, before any name has {t.min_history_bars} bars). This is expected, not an error.
            </span>
          </div>
        ) : null}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <DefinedMetric
            label="Admitted"
            tone="text-pos"
            testId="universe-diagnostic-admitted"
            value={diagnostic.admitted_count}
            definition={`Members resolved at the as-of (of ${diagnostic.candidate_pool_count} candidate-pool names).`}
          />
          {reasons.map((r) => (
            <DefinedMetric
              key={r.key}
              label={r.label}
              tone={r.value > 0 ? "text-text" : "text-text-faint"}
              testId={`universe-diagnostic-${r.key}`}
              value={r.value}
              definition={r.defn}
            />
          ))}
        </div>
        <p className="text-xs text-text-muted">
          A sub-threshold or short-history candidate is honestly EXCLUDED with a reason — never scored on
          fabricated or padded values. Excluded total:{" "}
          <span className="num text-text">{diagnostic.excluded_total}</span> of{" "}
          <span className="num text-text">{diagnostic.candidate_pool_count}</span> pool candidates.
        </p>
      </div>
    </Card>
  );
}

/** J-99 — human month labels for the membership-timeline Month dropdown (the option VALUE stays the ISO
 *  `MM` so the filter matches `date.slice(5,7)` exactly; only the visible label is friendly). */
const MONTH_NAMES: Record<string, string> = {
  "01": "Jan",
  "02": "Feb",
  "03": "Mar",
  "04": "Apr",
  "05": "May",
  "06": "Jun",
  "07": "Jul",
  "08": "Aug",
  "09": "Sep",
  "10": "Oct",
  "11": "Nov",
  "12": "Dec",
};

/** J-96 — the dynamic-universe membership timeline. Renders the resolved universe SIZE across the snapshot
 *  dates as a step-function chart (the J-44/J-49 overlay treatment), the per-date entries / exits, and the
 *  per-date excluded-by-reason counts, plus the three HONEST labels verbatim (the candidate-pool
 *  survivorship caveat, the warm-up boundary, and the universe-relative breadth caveat). Read-only
 *  descriptive metadata over the stored membership; an empty DB renders an honest empty timeline. */
function MembershipTimelinePanel({ timeline }: { timeline: MembershipTimeline }) {
  const points = timeline.points;
  const labels = timeline.labels;
  const maxSize = Math.max(1, ...points.map((p) => p.size));

  // J-99 — pure client-side VIEW TRANSFORM over the already-served `points`: Year/Month list filters +
  // 10-rows/page pagination, newest-first. These are list controls (NOT the global as-of switcher); they
  // hold only local view state and never re-derive any per-date size/entries/exits/excluded value. The
  // filtered+paged rows are a verbatim slice of `points` (Single source of truth; No recompute; J-18).
  const [year, setYear] = useState<string>(ALL_SENTINEL);
  const [month, setMonth] = useState<string>(ALL_SENTINEL);
  const [page, setPage] = useState(1);

  const yearOptions = useMemo(() => deriveYearOptions(points), [points]);
  const monthOptions = useMemo(() => deriveMonthOptions(points, year), [points, year]);
  const filtered = useMemo(() => filterTimelinePoints(points, year, month), [points, year, month]);
  const view = useMemo(() => paginateTimelinePoints(filtered, page), [filtered, page]);

  // Reset to page 1 whenever a filter changes (no orphaned page index past the new last page). The page
  // index itself is also clamped inside paginateTimelinePoints, so the render is always in-bounds.
  function onYearChange(next: string) {
    setYear(next);
    setMonth(ALL_SENTINEL); // months are year-scoped; drop a now-invalid month selection
    setPage(1);
  }
  function onMonthChange(next: string) {
    setMonth(next);
    setPage(1);
  }
  // Step the displayed page within bounds (paginateTimelinePoints re-clamps on render regardless).
  function goPrev() {
    setPage((p) => Math.max(1, p - 1));
  }
  function goNext() {
    setPage((p) => Math.min(view.pageCount, p + 1));
  }
  const monthLabel = (mm: string) => MONTH_NAMES[mm] ?? mm;
  // a compact step-function SVG sparkline of the resolved size over the snapshot dates.
  const W = 640;
  const H = 120;
  const padX = 8;
  const padY = 10;
  const innerW = W - padX * 2;
  const innerH = H - padY * 2;
  const stepPoints: string[] = [];
  if (points.length > 0) {
    points.forEach((p, i) => {
      const x0 = padX + (points.length === 1 ? innerW / 2 : (i / points.length) * innerW);
      const x1 = padX + (points.length === 1 ? innerW : ((i + 1) / points.length) * innerW);
      const y = padY + innerH - (p.size / maxSize) * innerH;
      stepPoints.push(`${x0.toFixed(1)},${y.toFixed(1)}`);
      stepPoints.push(`${x1.toFixed(1)},${y.toFixed(1)}`); // hold the level → step function
    });
  }
  return (
    <Card className="p-0" data-testid="membership-timeline-panel">
      <PanelTitle hint="How the point-in-time scored universe grew across the snapshot dates — its size at each date (a step function), which names entered/exited on which date, and why a date's size is what it is. Read-only; observed causally from each date's own snapshot.">
        <span className="inline-flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-text-faint" aria-hidden />
          Dynamic-universe membership timeline
        </span>
      </PanelTitle>
      <div className="space-y-4 p-4">
        {/* the three honest labels — carried VERBATIM from the backend (the UI re-types none of this) */}
        <div className="space-y-2 text-xs">
          <p
            className="rounded-md border border-border bg-surface-2 px-3 py-2 text-text-muted"
            data-testid="timeline-label-survivorship"
          >
            <span className="font-semibold text-text">Survivorship: </span>
            {labels.survivorship.label}
          </p>
          <p
            className="rounded-md border border-border bg-surface-2 px-3 py-2 text-text-muted"
            data-testid="timeline-label-warmup"
          >
            <span className="font-semibold text-text">Warm-up: </span>
            {labels.warmup.label}
          </p>
          <p
            className="rounded-md border border-border bg-surface-2 px-3 py-2 text-text-muted"
            data-testid="timeline-label-universe-relative"
          >
            <span className="font-semibold text-text">Universe-relative: </span>
            {labels.universe_relative}
          </p>
        </div>

        {points.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="No snapshots yet"
            description="Once snapshots exist, the resolved-universe size over time appears here. No fabricated dates or members are shown."
          />
        ) : (
          <>
            {/* the resolved-size step function (J-44/J-49 overlay treatment; design-token palette) */}
            <div className="rounded-md border border-border bg-surface-2 p-3" data-testid="timeline-step-chart">
              <div className="mb-1 flex items-center justify-between text-xs text-text-faint">
                <span>Resolved universe size</span>
                <span className="num">max {maxSize}</span>
              </div>
              <svg
                viewBox={`0 0 ${W} ${H}`}
                className="h-32 w-full"
                preserveAspectRatio="none"
                role="img"
                aria-label="Resolved universe size step function over the snapshot dates"
              >
                <polyline
                  points={stepPoints.join(" ")}
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
              <div className="mt-1 flex items-center justify-between text-[10px] text-text-faint">
                <span className="num">{formatIsoDate(points[0].date)}</span>
                <span className="num">{formatIsoDate(points[points.length - 1].date)}</span>
              </div>
            </div>

            {/* J-99 — Year/Month list filters + page readouts. These are pure VIEW TRANSFORMS over the
                already-served `points`; they narrow/page only the rendered rows and recompute no per-date
                value. They are NOT the global as-of switcher (J-18) — no date state is written. */}
            <div
              className="flex flex-wrap items-center justify-between gap-3"
              data-testid="timeline-controls"
            >
              <div className="flex flex-wrap items-center gap-2">
                <label className="flex flex-col gap-1 text-xs text-text-muted">
                  Year
                  <Select
                    aria-label="Filter membership timeline by year"
                    data-testid="timeline-year-filter"
                    className="w-32"
                    value={year}
                    onChange={(e) => onYearChange(e.target.value)}
                  >
                    <option value={ALL_SENTINEL}>All years</option>
                    {yearOptions.map((y) => (
                      <option key={y} value={y}>
                        {y}
                      </option>
                    ))}
                  </Select>
                </label>
                <label className="flex flex-col gap-1 text-xs text-text-muted">
                  Month
                  <Select
                    aria-label="Filter membership timeline by month"
                    data-testid="timeline-month-filter"
                    className="w-32"
                    value={month}
                    onChange={(e) => onMonthChange(e.target.value)}
                  >
                    <option value={ALL_SENTINEL}>All months</option>
                    {monthOptions.map((m) => (
                      <option key={m} value={m}>
                        {monthLabel(m)}
                      </option>
                    ))}
                  </Select>
                </label>
              </div>
              {/* Honest readout: how many dates this filtered/paged view shows out of the full payload. */}
              <p
                className="text-xs text-text-faint"
                aria-label="Filtered date count"
                data-testid="timeline-count-readout"
              >
                Showing{" "}
                <span className="num text-text-muted">{view.rows.length}</span> of{" "}
                <span className="num text-text-muted">{view.total}</span>{" "}
                {view.total === 1 ? "date" : "dates"}
                {view.total !== points.length ? (
                  <>
                    {" "}
                    (filtered from <span className="num text-text-muted">{points.length}</span>)
                  </>
                ) : null}
              </p>
            </div>

            {/* the per-date table: size + entries/exits + excluded-by-reason counts — now the filtered+paged
                slice of `points` rather than the full reversed list. */}
            {view.isEmpty ? (
              <div data-testid="timeline-empty-filter">
                <EmptyState
                  icon={TrendingUp}
                  title="No snapshot dates match this filter"
                  description="No fabricated dates are shown. Clear the Year/Month filter to see the full timeline again."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm" data-testid="timeline-table">
                  <thead>
                    <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                      <th className="px-3 py-2 font-medium">Snapshot date</th>
                      <th className="px-3 py-2 text-right font-medium">Size</th>
                      <th className="px-3 py-2 font-medium">Entries</th>
                      <th className="px-3 py-2 font-medium">Exits</th>
                      <th className="px-3 py-2 text-right font-medium">Excl. hist / stale / price / liq</th>
                    </tr>
                  </thead>
                  <tbody>
                    {view.rows.map((p) => (
                      <tr
                        key={p.date}
                        className="border-b border-border last:border-b-0"
                        data-testid={`timeline-row-${p.date}`}
                      >
                        <td className="px-3 py-2 num text-text">{formatIsoDate(p.date)}</td>
                        <td className="px-3 py-2 num text-right font-semibold text-text">{p.size}</td>
                        <td className="px-3 py-2 text-xs text-pos">
                          {p.entries.length > 0 ? (
                            <span className="num">
                              +{p.entries.length}
                              <span className="ml-1 text-text-faint">
                                {p.entries.slice(0, 6).join(", ")}
                                {p.entries.length > 6 ? "…" : ""}
                              </span>
                            </span>
                          ) : (
                            <span className="text-text-faint">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-xs text-neg">
                          {p.exits.length > 0 ? (
                            <span className="num">
                              −{p.exits.length}
                              <span className="ml-1 text-text-faint">
                                {p.exits.slice(0, 6).join(", ")}
                                {p.exits.length > 6 ? "…" : ""}
                              </span>
                            </span>
                          ) : (
                            <span className="text-text-faint">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2 num text-right text-xs text-text-muted">
                          {p.excluded.below_history} / {p.excluded.stale_series ?? 0} / {p.excluded.below_price} /{" "}
                          {p.excluded.below_adv}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* J-99 — pagination controls: prev/next (disabled at the bounds) + "Page x of N". */}
            {!view.isEmpty && view.pageCount > 1 ? (
              <div
                className="flex items-center justify-between gap-3"
                data-testid="timeline-pagination"
              >
                <button
                  type="button"
                  onClick={goPrev}
                  disabled={view.page <= 1}
                  aria-label="Previous page of snapshot dates"
                  data-testid="timeline-prev-page"
                  className={cn(
                    "inline-flex h-8 items-center gap-1 rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text-muted transition",
                    "hover:border-border-strong focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                >
                  <ChevronLeft className="h-3.5 w-3.5" aria-hidden />
                  Prev
                </button>
                <span
                  className="text-xs text-text-muted"
                  aria-label="Current page"
                  data-testid="timeline-page-readout"
                >
                  Page <span className="num text-text">{view.page}</span> of{" "}
                  <span className="num text-text">{view.pageCount}</span>
                </span>
                <button
                  type="button"
                  onClick={goNext}
                  disabled={view.page >= view.pageCount}
                  aria-label="Next page of snapshot dates"
                  data-testid="timeline-next-page"
                  className={cn(
                    "inline-flex h-8 items-center gap-1 rounded-md border border-border bg-surface-2 px-3 text-xs font-medium text-text-muted transition",
                    "hover:border-border-strong focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                </button>
              </div>
            ) : null}
          </>
        )}
      </div>
    </Card>
  );
}

/** J-95 — the confirm-gated "extend history backward" control. It reuses the rebuild confirm chrome + the
 *  live job card (no second progress surface). Extending history backward is a best-effort `both` job over
 *  an earlier price start; the real backward-history fetch is DATA-WALLED on this host, so the panel states
 *  the honest blocked/limited-coverage (NA) outcome up front and carries the candidate-pool survivorship
 *  caveat. Once earlier bars DO land, the point-in-time resolver admits names earlier automatically (no
 *  separate membership recompute). The committed price seed is never deleted by the clear step. */
function BackwardHistoryPanel({
  survivorship,
  priceStart,
  running,
  onStarted,
}: {
  survivorship: PoolSurvivorship;
  priceStart: string | null;
  running: boolean;
  onStarted: (job: DataJob) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [naNote, setNaNote] = useState<string | null>(null);
  // a sensible earlier target start: one calendar year before the current price start (a placeholder the
  // operator can interpret; the actual fetch is provider-gated and best-effort).
  const targetStart = priceStart
    ? `${(parseInt(priceStart.slice(0, 4), 10) - 1).toString()}${priceStart.slice(4)}`
    : null;

  async function handleConfirm() {
    if (starting || running) return;
    setStarting(true);
    setError(null);
    setNaNote(null);
    try {
      if (!targetStart || !priceStart) {
        setNaNote("No committed price start yet — nothing to extend backward.");
        setConfirming(false);
        return;
      }
      // a best-effort `both` job over the earlier window (fetch earlier bars, then backfill snapshots).
      // The fetch is data-walled on this host → the live job card surfaces the honest blocked / partial
      // (NA) outcome; this is non-halting (it never drives a STALLED state).
      const resp = await startDataJob("both", targetStart, priceStart);
      const snap = await fetchDataJob(resp.job_id);
      onStarted(snap);
      setConfirming(false);
      setNaNote(
        "Backward-history fetch started (best-effort). If the provider is unreachable on this host, the " +
          "job card will show an honest blocked / limited-coverage (NA) outcome — no fabricated bars, and " +
          "the loop is never halted. Once earlier bars land, the universe resolves further back automatically.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the backward-history extension.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <Card className="p-0" data-testid="backward-history-panel">
      <PanelTitle hint="Extend committed price history backward (an earlier start) so the point-in-time universe resolves further into the past — reusing the chunked import + rebuild path. Best-effort: a walled provider yields an honest blocked / limited-coverage (NA) state, never fabricated bars. The committed price seed is never deleted.">
        <span className="inline-flex items-center gap-2">
          <History className="h-4 w-4 text-text-faint" aria-hidden />
          Extend history backward
        </span>
      </PanelTitle>
      <div className="space-y-3 p-4 text-sm">
        <p
          className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted"
          data-testid="backward-history-survivorship"
        >
          <span className="font-semibold text-text">Survivorship caveat: </span>
          {survivorship.label}
        </p>
        <Metric
          label="Current price start"
          value={priceStart ? formatIsoDate(priceStart) : "—"}
        />
        <p className="text-xs text-text-muted">
          Extending backward fetches earlier real EOD bars (best-effort) then rebuilds snapshots; the
          point-in-time resolver then admits names from earlier dates automatically. A true point-in-time
          index-constituent feed is a separate, data-dependent enhancement — never fabricated when absent.
        </p>
        <button
          type="button"
          onClick={() => setConfirming(true)}
          disabled={running || starting || !priceStart}
          data-testid="backward-history-button"
          className={cn(
            "inline-flex h-9 items-center gap-2 rounded-md border px-4 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            running || starting || !priceStart
              ? "cursor-not-allowed border-border text-text-faint"
              : "border-accent text-accent hover:bg-surface-2",
          )}
        >
          <History className="h-4 w-4" aria-hidden />
          Extend history backward
        </button>
        {naNote ? (
          <p className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted" data-testid="backward-history-na">
            {naNote}
          </p>
        ) : null}
        {error ? (
          <p role="alert" className="flex items-center gap-2 text-xs text-neg">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
            {error}
          </p>
        ) : null}
      </div>
      {confirming ? (
        <BackwardHistoryConfirmModal
          targetStart={targetStart}
          priceStart={priceStart}
          starting={starting}
          error={error}
          onCancel={() => {
            setConfirming(false);
            setError(null);
          }}
          onConfirm={handleConfirm}
        />
      ) : null}
    </Card>
  );
}

/** The confirm modal for the J-95 backward-history extension — the rebuild-modal chrome, restating the
 *  best-effort / data-walled / seed-never-deleted contract so the action is never a surprise. */
function BackwardHistoryConfirmModal({
  targetStart,
  priceStart,
  starting,
  error,
  onCancel,
  onConfirm,
}: {
  targetStart: string | null;
  priceStart: string | null;
  starting: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(10,14,20,0.8)] p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Confirm backward-history extension"
      data-testid="backward-history-confirm-modal"
    >
      <Card className="w-full max-w-lg p-0 shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-accent">
            <History className="h-4 w-4" aria-hidden />
            Confirm backward-history extension
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
        <div className="max-h-[55vh] space-y-3 overflow-y-auto p-4 text-sm">
          <p className="text-text-muted">
            This attempts a best-effort fetch of earlier real EOD bars
            {targetStart && priceStart ? ` (${formatIsoDate(targetStart)} → ${formatIsoDate(priceStart)})` : ""}
            , then rebuilds snapshots over the resolved universe.
          </p>
          <ul className="list-disc space-y-1 pl-5 text-xs text-text-faint">
            <li>The committed price seed is never deleted — only earlier bars are added + snapshots regenerated.</li>
            <li>No canonical formula changes — only how far back the point-in-time universe can resolve.</li>
            <li>
              If the provider is unreachable on this host, the job ends in an honest blocked / limited-coverage
              (NA) state — no fabricated bars, and the loop is never halted.
            </li>
          </ul>
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
            disabled={starting}
            data-testid="backward-history-confirm-button"
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md border border-accent bg-accent/10 px-4 text-sm font-semibold text-accent transition hover:bg-accent/20 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              starting && "cursor-not-allowed opacity-60",
            )}
          >
            {starting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <History className="h-4 w-4" aria-hidden />}
            {starting ? "Starting…" : "Extend history backward"}
          </button>
        </div>
      </Card>
    </div>
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
  // Start is blocked while busy/running or with an empty/INVALID date.
  const disabled = busy || running || !start || !end || !startValid || !endValid;
  return (
    <Card className="p-0">
      <PanelTitle hint="Pick a date or range (typed as yyyy-MM-dd), a job kind, and — for a fetch — an import source. These date inputs are job parameters — they do NOT change the global as-of viewing date.">
        Start a fetch / backfill job
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
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label} · {s.available ? "available" : "needs key"}
                  </option>
                ))}
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
          import source, covering the full committed symbol pool. A provider failure is surfaced
          explicitly and fabricates nothing.
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

/** ops-hardening iter-1 (J-01) — the four-way exclusion breakdown inline text for a backfill/both/
 *  rebuild run: calendar days, already-snapshotted, non-trading, and error counts. Renders nothing when
 *  every field is absent/null (a fetch/expand run never populates them) — never a fabricated "0". Pure
 *  re-formatting of backend-computed counts; no arithmetic happens here beyond string joining. Shared
 *  between the Job progress panel and the Run history table so both read the SAME breakdown shape. */
function BackfillBreakdown({
  calendarDays,
  alreadySnapshotted,
  nonTradingDays,
  errorOther,
}: {
  calendarDays: number | null | undefined;
  alreadySnapshotted: number | null | undefined;
  nonTradingDays: number | null | undefined;
  errorOther: number | null | undefined;
}) {
  if (calendarDays == null && alreadySnapshotted == null && nonTradingDays == null && errorOther == null) {
    return null;
  }
  const parts: string[] = [];
  if (calendarDays != null) parts.push(`${calendarDays} calendar day${calendarDays === 1 ? "" : "s"}`);
  if (alreadySnapshotted != null) parts.push(`${alreadySnapshotted} already snapshotted`);
  if (nonTradingDays != null) parts.push(`${nonTradingDays} non-trading`);
  if (errorOther) parts.push(`${errorOther} error${errorOther === 1 ? "" : "s"}`);
  return (
    <p className="num text-xs text-text-faint" data-testid="backfill-breakdown">
      {parts.join(" · ")}
    </p>
  );
}

/** TC-6 (ops-hardening iter-1) — the reduced persisted-run view the Job progress panel falls back to
 *  when persisted run history exists but no job has started THIS browser session. Built from `DataRun`
 *  fields only (status, message, the breakdown counts) — a persisted row carries no
 *  `symbols_total`/`chunk_index`/`chunk_total`, so this is its OWN small view, never a forced fit into
 *  the live `DataJob` rendering above. */
function LastRunSummary({ run }: { run: DataRun }) {
  return (
    <Card className="p-0">
      <PanelTitle
        hint={`${run.kind ?? "seed load"} job · ${
          run.start && run.end ? `${fmtDate(run.start)} → ${fmtDate(run.end)}` : "—"
        } · from a previous session`}
      >
        Job progress
      </PanelTitle>
      <div className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge
            variant={runStatusVariant(run.kind, run.status, run.snapshots_created)}
            className="num gap-1.5"
            data-testid="last-run-status"
          >
            {runStatusLabel(run.kind, run.status, run.snapshots_created)}
          </Badge>
          <span className="num text-xs text-text-muted">{run.message}</span>
        </div>
        <p className="num text-xs text-text-faint">
          {run.snapshots_created ?? "—"} snapshots · {run.dates_total ?? "—"} trading days in range
        </p>
        <BackfillBreakdown
          calendarDays={run.calendar_days}
          alreadySnapshotted={run.already_snapshotted}
          nonTradingDays={run.non_trading_days}
          errorOther={run.error_other}
        />
      </div>
    </Card>
  );
}

function JobProgressPanel({
  job,
  runs,
  sources,
  onResumed,
  heartbeatStaleSeconds,
}: {
  job: DataJob | null;
  runs: DataRun[];
  sources: ProviderSource[];
  onResumed: (importId: string) => void;
  heartbeatStaleSeconds: number;
}) {
  if (!job) {
    if (runs.length === 0) {
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
    // TC-6 (ops-hardening iter-1): persisted run history exists even though no job has started THIS
    // browser session — render the most recent persisted run's outcome instead of the empty copy above.
    // `runs` is already newest-first (GET /api/data's `recent_runs`), so `runs[0]` is the latest.
    return <LastRunSummary run={runs[0]} />;
  }

  // A fetch/both shows the fetch bar; a backfill shows the snapshot bar.
  const showFetch = job.kind === "fetch" || job.kind === "both";
  const showBackfill = job.kind === "backfill" || job.kind === "both";
  const paused = job.status === "resumable"; // J-34: a rate-limited graceful pause (amber, not failed)
  const failed = job.status === "failed" || job.status === "partial";
  const chunkTotal = job.chunk_total ?? 0;
  const symbolsRemaining = Math.max(job.symbols_total - job.symbols_ok - job.symbols_failed, 0);
  const jobSource = sources.find((s) => s.id === job.source);
  const zeroWork = isZeroWorkRun(job.kind, job.status, job.snapshots_created);

  return (
    <Card className="p-0">
      <PanelTitle
        hint={`${job.kind} job · ${job.source ? `${job.source} · ` : ""}${fmtDate(job.start)} → ${fmtDate(job.end)}`}
      >
        Job progress
      </PanelTitle>
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={runStatusVariant(job.kind, job.status, job.snapshots_created)} className="num gap-1.5" data-testid="job-status">
            {job.status === "running" ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : null}
            {paused ? "rate-limited — resumable" : runStatusLabel(job.kind, job.status, job.snapshots_created)}
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
            <BackfillBreakdown
              calendarDays={job.calendar_days}
              alreadySnapshotted={job.already_snapshotted}
              nonTradingDays={job.non_trading_days}
              errorOther={job.error_other}
            />
            {zeroWork ? (
              <p
                className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted"
                data-testid="zero-work-note"
              >
                Zero-work outcome — every requested trading day already had a snapshot (or the range
                contains no trading days). No new computation was needed; this is not a failure.
              </p>
            ) : null}
          </div>
        ) : null}

        <StageTimings job={job} />

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
                <Badge
                  variant={runStatusVariant(run.kind, run.status, run.snapshots_created)}
                  className="num"
                  data-testid="run-status"
                >
                  {/* J-60: running (in-flight from job start) / interrupted (orphan swept on boot) read
                      alongside the terminal ok/partial/failed states. ops-hardening iter-1: a zero-work
                      backfill/both/rebuild `ok` run reads distinctly ("no new snapshots"), never the same
                      unexplained green success badge as a productive run. */}
                  {run.status === "running" ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" aria-hidden />
                  ) : null}
                  {runStatusLabel(run.kind, run.status, run.snapshots_created)}
                </Badge>
              </td>
              <td className="num px-3 py-2 text-right">
                <span className="text-pos">{run.symbols_ok}</span>
                <span className="text-text-faint"> / </span>
                <span className={run.symbols_failed > 0 ? "text-neg" : "text-text-muted"}>{run.symbols_failed}</span>
              </td>
              <td className="num px-3 py-2 text-right text-text-muted">
                {run.snapshots_created ?? "—"}
                <BackfillBreakdown
                  calendarDays={run.calendar_days}
                  alreadySnapshotted={run.already_snapshotted}
                  nonTradingDays={run.non_trading_days}
                  errorOther={run.error_other}
                />
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
