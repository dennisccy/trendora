"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, ArrowUpRight, ShieldAlert } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import type { VariantProps } from "class-variance-authority";

import { Badge, type badgeVariants } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { phaseFillVar } from "@/lib/phase";
import { cn } from "@/lib/utils";
import {
  fetchMarketPhase,
  type MarketPhaseComponent,
  type MarketPhaseEpisode,
  type MarketPhaseResponse,
  type MarketPhaseRecoveryTurn,
  type MarketPhaseRetrospective,
  type MarketPhaseTimelinePoint,
} from "@/lib/api";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/**
 * J-87 + J-88 dashboard "Market Phase & Severity" panel. It renders, for the SINGLE global as-of date,
 * the market's discrete phase (Expansion / Pullback / Correction / Bear / Recovery), a 0-100 severity
 * score with its NAMED component breakdown (explainable — never a bare number), and a deterministic
 * 0-1 filtered P(bear) with its observation vector disclosed.
 *
 * Single source of truth: every value comes verbatim from `GET /api/market-phase` (computed once by the
 * read-only `market_phase` derivation, cached behind dataset_version). The frontend recomputes NOTHING —
 * the regime input the severity reads is the SAME stored regime the Dashboard regime card shows (J-06).
 *
 * Exactly one date selector (J-18): this panel reads the single global as-of from `useAsOf()` only — it
 * holds NO second date `useState` and adds NO window/document keydown listener. It re-points with the
 * global as-of like every other date-scoped surface.
 */

/** The phase label -> Badge palette variant, grouped by stress posture: Expansion/Recovery -> ok (green);
 *  Pullback -> warn (amber); Correction/Bear -> danger (red). Presentation only — one label, one colour. */
function phaseVariant(phase: string | null): BadgeVariant {
  if (phase === "Bear" || phase === "Correction") return "danger";
  if (phase === "Pullback") return "warn";
  return "ok"; // Expansion · Recovery (calm / rebounding)
}

// iter-38 (J-97): the phase label → fill-token mapping now lives in the ONE shared `lib/phase` module
// (`phaseFillVar`), imported above, so the card timeline band and the J-97 cross-view chart phase bands
// read the SAME label→colour mapping (coherence: same date ⇒ same colour everywhere). No second mapping.

/** Human labels for the five named severity component keys (presentation only — values are computed once
 *  in the backend engine and only re-formatted here). */
const COMPONENT_LABELS: Record<string, string> = {
  drawdown_depth: "Drawdown depth",
  time_underwater: "Time underwater",
  regime_risk: "Market regime (stored)",
  breadth_below_200dma: "Breadth below 200-DMA",
  vix_gate: "VIX stress gate",
};

function componentLabel(name: string): string {
  return COMPONENT_LABELS[name] ?? name;
}

function fmtPct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "NA";
}

export function MarketPhaseCard() {
  const { asOf } = useAsOf();
  const [data, setData] = useState<MarketPhaseResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  // J-89: the fenced retrospective (full-sample / analysis-only) sub-view toggle. OFF by default — the
  // heavy backward-smoother only runs when the user opts into the analysis-only view. NOT a date state.
  const [showRetrospective, setShowRetrospective] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    const asof = asOf ?? undefined; // historical date or latest — the single global as-of
    // J-89: request the fenced retrospective ADDITIVELY only when the sub-view is toggled on.
    fetchMarketPhase(asof, controller.signal, showRetrospective)
      .then((res) => {
        setData(res);
        setStatus("ok");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [asOf, showRetrospective]);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <CardTitle className="flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-text-faint" aria-hidden />
            Market Phase &amp; Severity
          </CardTitle>
          {data ? (
            <span className="num text-xs text-text-faint">as of {formatIsoDate(data.asof_date)}</span>
          ) : null}
        </div>
        {status === "ok" && data && data.available ? (
          <div className="flex items-center gap-2">
            <Badge variant={phaseVariant(data.phase)}>{data.phase}</Badge>
            <PBearBadge pBear={data.p_bear} />
          </div>
        ) : null}
      </CardHeader>
      <CardContent>
        {status === "loading" ? (
          <div className="h-44 w-full animate-pulse rounded bg-surface-2" />
        ) : null}

        {status === "error" ? (
          <div className="flex h-44 items-center gap-3 rounded border border-warn bg-surface p-5 text-sm text-warn">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Market phase unavailable</p>
              <p className="text-text-muted">
                The market-phase layer could not load from the API. Nothing is fabricated — confirm the
                backend is running and reload.
              </p>
            </div>
          </div>
        ) : null}

        {status === "ok" && data && !data.available ? (
          <div className="flex flex-col gap-4">
            <div className="flex h-44 flex-col items-center justify-center gap-2 text-sm text-text-muted">
              <Activity className="h-8 w-8 text-text-faint" aria-hidden />
              <p>Not enough history to derive a market phase for this date.</p>
              <p className="text-xs text-text-faint">
                A window with fewer than {data.min_history_bars} benchmark bars is reported NA — never a
                fabricated phase or probability. The phase timeline is honestly empty for this date.
              </p>
            </div>
            <RecoveryTurnLine recoveryTurn={data.recovery_turn} />
          </div>
        ) : null}

        {status === "ok" && data && data.available ? (
          <MarketPhaseBody
            data={data}
            showRetrospective={showRetrospective}
            onToggleRetrospective={() => setShowRetrospective((prev) => !prev)}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

/** The 0-1 filtered P(bear) badge (J-88) — coloured by level (>= 2/3 danger, >= 1/3 warn, else ok). The
 *  thresholds here are PRESENTATION-only colour bands for a probability the backend computed; they tune
 *  no value. */
function PBearBadge({ pBear }: { pBear: number | null }) {
  if (typeof pBear !== "number") {
    return <Badge variant="default" className="num">P(bear) NA</Badge>;
  }
  const variant: BadgeVariant = pBear >= 2 / 3 ? "danger" : pBear >= 1 / 3 ? "warn" : "ok";
  return (
    <Badge variant={variant} className="num">
      P(bear) {pBear.toFixed(2)}
    </Badge>
  );
}

function MarketPhaseBody({
  data,
  showRetrospective,
  onToggleRetrospective,
}: {
  data: MarketPhaseResponse;
  showRetrospective: boolean;
  onToggleRetrospective: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* severity headline + cycle legs */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <span className="num text-4xl font-semibold text-text">
            {data.severity != null ? data.severity.toFixed(2) : "NA"}
          </span>
          <span className="text-sm text-text-muted">/ 100 severity</span>
        </div>
        <div className="flex flex-col items-end gap-0.5 text-xs text-text-muted">
          <span className="num">Drawdown {fmtPct(data.drawdown_pct)}</span>
          <span className="num">Off trough {fmtPct(data.off_trough_pct)}</span>
        </div>
      </div>

      {/* J-90: the causal recovery/turn signal for the resolved as-of (explainable, never a bare flag) */}
      <RecoveryTurnLine recoveryTurn={data.recovery_turn} />

      {/* named component breakdown — explainability, never a bare number */}
      <SeverityBreakdown components={data.components} />

      {/* J-89: the per-date market-phase + filtered P(bear) history timeline (step function) */}
      <PhaseTimeline data={data} />

      {/* J-89: the dated causal downtrend-episode list */}
      <DowntrendEpisodes episodes={data.episodes ?? []} />

      {/* J-89: the FENCED retrospective (full-sample / analysis-only) sub-view toggle + body */}
      <RetrospectivePanel
        retrospective={data.retrospective}
        show={showRetrospective}
        onToggle={onToggleRetrospective}
      />

      {/* the disclosed P(bear) observation vector (J-88) */}
      <ObservationVector data={data} />
    </div>
  );
}

/** J-90: the causal recovery/turn signal line — a coloured badge + its config-defined triggering reason
 *  (explainable, never a bare flag). Reads the SAME `GET /api/market-phase` payload. */
function RecoveryTurnLine({ recoveryTurn }: { recoveryTurn?: MarketPhaseRecoveryTurn }) {
  if (!recoveryTurn) return null;
  const isTurn = recoveryTurn.is_recovery_turn;
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded border p-2.5 text-xs",
        isTurn
          ? "border-pos/40 bg-pos/5 text-pos"
          : "border-border bg-surface-2 text-text-muted",
      )}
    >
      {isTurn ? (
        <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      ) : (
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-text-faint" aria-hidden />
      )}
      <div className="space-y-0.5">
        <p className="font-medium">
          {isTurn ? "Recovery / turn signalled" : "No recovery turn at this date"}
        </p>
        <p className={cn(isTurn ? "text-pos/80" : "text-text-faint")}>{recoveryTurn.reason}</p>
      </div>
    </div>
  );
}

/** J-89: the market-phase HISTORY timeline — a per-snapshot-date step function of the J-87 phase (the
 *  colored band) + the J-88 filtered P(bear) (the overlaid line), read from the SAME single served series.
 *  Drawn as a compact SVG: a phase-colored band behind a P(bear) polyline, with the most recent date
 *  (the resolved as-of) marked. Honest empty when no causal dates exist. */
function PhaseTimeline({ data }: { data: MarketPhaseResponse }) {
  const timeline = data.timeline ?? [];
  if (timeline.length === 0) {
    return (
      <p className="text-xs text-text-faint">
        No market-phase timeline for this date — the causal history is honestly empty (never fabricated).
      </p>
    );
  }
  const total = data.total_timeline_dates ?? timeline.length;
  const showingTail = total > timeline.length;

  const width = 100; // viewBox units (responsive via preserveAspectRatio="none")
  const height = 40;
  const n = timeline.length;
  // x position per point (evenly spaced); the step band fills [x_i, x_{i+1}) with the phase colour.
  const xAt = (i: number) => (n <= 1 ? width / 2 : (i / (n - 1)) * width);
  // P(bear) line: y inverts (0 at bottom, 1 at top).
  const yAt = (p: number) => height - p * height;

  const linePoints = timeline.map((pt, i) => `${xAt(i)},${yAt(pt.p_bear)}`).join(" ");

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-text-faint">
          Phase &amp; P(bear) timeline
          {showingTail ? ` · latest ${timeline.length} of ${total}` : ` (${total})`}
        </p>
        <PhaseLegend labels={data.labels} />
      </div>
      <div className="relative w-full overflow-hidden rounded border border-border bg-surface-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          className="block h-24 w-full"
          role="img"
          aria-label="Market-phase and filtered P(bear) step-function timeline"
        >
          {/* phase-colored step band (J-87 phase per date) */}
          {timeline.map((pt, i) => {
            const x0 = i === 0 ? 0 : (xAt(i - 1) + xAt(i)) / 2;
            const x1 = i === n - 1 ? width : (xAt(i) + xAt(i + 1)) / 2;
            return (
              <rect
                key={`band-${pt.date}`}
                x={x0}
                y={0}
                width={Math.max(0, x1 - x0)}
                height={height}
                fill={phaseFillVar(pt.phase)}
                opacity={0.18}
              />
            );
          })}
          {/* the filtered P(bear) line (J-88) over the band — the causal forward probability */}
          <polyline
            points={linePoints}
            fill="none"
            stroke="var(--accent)"
            strokeWidth={0.8}
            vectorEffect="non-scaling-stroke"
          />
          {/* the resolved as-of marker (the latest causal date) — J-49 marker treatment */}
          <line
            x1={xAt(n - 1)}
            y1={0}
            x2={xAt(n - 1)}
            y2={height}
            stroke="var(--text-faint)"
            strokeWidth={0.6}
            strokeDasharray="2 2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>
      <div className="flex justify-between text-[10px] text-text-faint">
        <span className="num">{formatIsoDate(timeline[0].date)}</span>
        <span>filtered P(bear) line · phase band · ↑ = higher bear probability</span>
        <span className="num">{formatIsoDate(timeline[n - 1].date)}</span>
      </div>
    </div>
  );
}

/** A compact swatch legend for the phase band colours (config-driven labels). */
function PhaseLegend({ labels }: { labels: string[] }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {labels.map((label) => (
        <span key={label} className="flex items-center gap-1 text-[10px] text-text-faint">
          <span
            className="inline-block h-2 w-2 rounded-sm"
            style={{ backgroundColor: phaseFillVar(label), opacity: 0.6 }}
          />
          {label}
        </span>
      ))}
    </div>
  );
}

/** J-89: the dated causal downtrend-episode list — each episode's first-trigger date, the severity at
 *  trigger, and whether it is still open at the resolved as-of (else closed on its last date). Honest
 *  empty list when no downtrend triggered ≤ D. */
function DowntrendEpisodes({ episodes }: { episodes: MarketPhaseEpisode[] }) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs uppercase tracking-wide text-text-faint">
        Causal downtrend episodes {episodes.length ? `(${episodes.length})` : ""}
      </p>
      {episodes.length === 0 ? (
        <p className="text-xs text-text-faint">
          No causal downtrend episode triggered up to this date.
        </p>
      ) : (
        <ul className="space-y-1">
          {episodes.map((ep) => (
            <li
              key={ep.first_trigger_date}
              className="flex flex-wrap items-center justify-between gap-2 rounded border border-border bg-surface-2 px-2.5 py-1.5 text-xs"
            >
              <span className="num text-text">
                {formatIsoDate(ep.first_trigger_date)} → {formatIsoDate(ep.last_date)}
              </span>
              <span className="flex items-center gap-2">
                <span className="num text-text-muted">
                  severity {ep.severity_at_trigger.toFixed(0)} · peak P(bear){" "}
                  {ep.peak_p_bear.toFixed(2)}
                </span>
                <Badge variant={ep.open ? "danger" : "default"}>{ep.open ? "open" : "closed"}</Badge>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** J-89: the FENCED retrospective (full-sample / analysis-only) sub-view. EXPLICITLY labelled analysis-only
 *  and visibly fenced from the causal path (the J-49 marker treatment): it shows the SMOOTHED P(bear) +
 *  the peak-to-trough true-bear dating, which are lookahead by construction and never feed any as-of value.
 *  Toggled off by default — the heavy backward-smoother runs only when opened. */
function RetrospectivePanel({
  retrospective,
  show,
  onToggle,
}: {
  retrospective?: MarketPhaseRetrospective;
  show: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="space-y-2 rounded border border-dashed border-border bg-surface-2/40 p-2.5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-text-muted">
          Retrospective (full-sample / analysis-only)
        </p>
        <button
          type="button"
          onClick={onToggle}
          aria-pressed={show}
          className={cn(
            "rounded border px-2 py-1 text-xs transition-colors",
            "hover:border-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 active:bg-surface",
            show ? "border-accent bg-accent/10 text-accent" : "border-border bg-surface text-text-muted",
          )}
        >
          {show ? "Hide" : "Show"} retrospective
        </button>
      </div>
      <p className="text-[11px] text-text-faint">
        Future-aware analysis only: the SMOOTHED probability + the peak-to-trough &quot;true bear&quot;
        dating use the full sample (information after each date) and are fenced from the causal as-of path —
        they never feed any score, signal, episode, or study.
      </p>
      {show ? <RetrospectiveBody retrospective={retrospective} /> : null}
    </div>
  );
}

function RetrospectiveBody({ retrospective }: { retrospective?: MarketPhaseRetrospective }) {
  if (!retrospective) {
    return <div className="h-16 w-full animate-pulse rounded bg-surface-2" />;
  }
  if (!retrospective.available) {
    return (
      <p className="text-xs text-text-faint">
        Not enough history for a retrospective analysis at this date (NA — never fabricated).
      </p>
    );
  }
  const smoothed = retrospective.smoothed;
  const episodes = retrospective.true_bear_episodes;
  return (
    <div className="space-y-3 pt-1">
      {/* smoothed P(bear) tail (analysis-only) */}
      <div className="space-y-1">
        <p className="text-[11px] uppercase tracking-wide text-text-faint">
          Smoothed P(bear) · full-sample
          {retrospective.total_smoothed_dates && retrospective.total_smoothed_dates > smoothed.length
            ? ` · latest ${smoothed.length} of ${retrospective.total_smoothed_dates}`
            : ""}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {smoothed.slice(-12).map((pt) => (
            <span
              key={pt.date}
              className="num rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] text-text-muted"
              title={`smoothed P(bear) ${pt.p_bear_smoothed.toFixed(2)} on ${formatIsoDate(pt.date)}`}
            >
              {formatIsoDate(pt.date)}: {pt.p_bear_smoothed.toFixed(2)}
            </span>
          ))}
        </div>
      </div>
      {/* peak-to-trough true-bear dating (analysis-only) */}
      <div className="space-y-1">
        <p className="text-[11px] uppercase tracking-wide text-text-faint">
          True-bear dating · peak → trough (≥ {retrospective.min_phase_days}d, ≥{" "}
          {retrospective.min_amplitude_pct}% drawdown)
        </p>
        {episodes.length === 0 ? (
          <p className="text-[11px] text-text-faint">
            No qualifying true-bear phase in the full sample (censored — never fabricated).
          </p>
        ) : (
          <ul className="space-y-1">
            {episodes.map((ep) => (
              <li
                key={ep.peak_date}
                className="flex flex-wrap items-center justify-between gap-2 rounded border border-border bg-surface px-2 py-1 text-[11px]"
              >
                <span className="num text-text-muted">
                  {formatIsoDate(ep.peak_date)} → {formatIsoDate(ep.trough_date)}
                </span>
                <span className="num text-neg">
                  {ep.drawdown_pct.toFixed(1)}% · {ep.duration_days}d
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/** The named severity component breakdown (mirrors ComponentBreakdown's three-column treatment) — every
 *  configured component shown with its [0,1] value + contribution; an NA component is honestly marked. */
function SeverityBreakdown({ components }: { components: MarketPhaseComponent[] }) {
  return (
    <div className="space-y-1.5">
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 text-xs uppercase tracking-wide text-text-faint">
        <span>Severity driver</span>
        <span className="text-right">Value</span>
        <span className="text-right">Contribution</span>
      </div>
      {components.map((component) => (
        <div
          key={component.name}
          className="grid grid-cols-[1fr_auto_auto] items-center gap-x-4 text-xs"
        >
          <span className="text-text-muted">{componentLabel(component.name)}</span>
          <span className={cn("num text-right", component.available ? "text-text-faint" : "text-warn")}>
            {component.available && component.value != null ? component.value.toFixed(2) : "NA"}
          </span>
          <span className="num text-right text-text">
            {component.contribution == null ? "—" : component.contribution.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

/** The forward-filter observation vector (J-88): one [0,1] stress reading per stored snapshot date <= D
 *  that the deterministic Hamilton filter ingested to produce P(bear). Disclosed so the probability is
 *  never a bare number. */
function ObservationVector({ data }: { data: MarketPhaseResponse }) {
  if (data.observations.length === 0) {
    return (
      <p className="text-xs text-text-faint">
        No filter observations available for this date — P(bear) reported NA, never fabricated.
      </p>
    );
  }
  const total = data.total_observations ?? data.observations.length;
  const showingTail = total > data.observations.length;
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-wide text-text-faint">
        Filter observations · drives P(bear)
        {showingTail
          ? ` · showing latest ${data.observations.length} of ${total}`
          : ` (${total})`}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {data.observations.map((obs) => (
          <span
            key={obs.date}
            className="num rounded border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted"
            title={`stress ${obs.reading.toFixed(2)} · P(bear) ${obs.p_bear.toFixed(2)} on ${formatIsoDate(obs.date)}`}
          >
            {formatIsoDate(obs.date)}: {obs.reading.toFixed(2)}
          </span>
        ))}
      </div>
      <p className="text-xs text-text-faint">
        Each is the [0,1] stress reading on a stored snapshot ≤ the as-of date; the forward filter
        consumes every observation ≤ D and is deterministic (committed params, never re-fit at serve time).
      </p>
    </div>
  );
}
