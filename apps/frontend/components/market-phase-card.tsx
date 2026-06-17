"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import type { VariantProps } from "class-variance-authority";

import { Badge, type badgeVariants } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";
import { fetchMarketPhase, type MarketPhaseComponent, type MarketPhaseResponse } from "@/lib/api";

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

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    const asof = asOf ?? undefined; // historical date or latest — the single global as-of
    fetchMarketPhase(asof, controller.signal)
      .then((res) => {
        setData(res);
        setStatus("ok");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [asOf]);

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
          <div className="flex h-44 flex-col items-center justify-center gap-2 text-sm text-text-muted">
            <Activity className="h-8 w-8 text-text-faint" aria-hidden />
            <p>Not enough history to derive a market phase for this date.</p>
            <p className="text-xs text-text-faint">
              A window with fewer than {data.min_history_bars} benchmark bars is reported NA — never a
              fabricated phase or probability.
            </p>
          </div>
        ) : null}

        {status === "ok" && data && data.available ? (
          <MarketPhaseBody data={data} />
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

function MarketPhaseBody({ data }: { data: MarketPhaseResponse }) {
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

      {/* named component breakdown — explainability, never a bare number */}
      <SeverityBreakdown components={data.components} />

      {/* the disclosed P(bear) observation vector (J-88) */}
      <ObservationVector data={data} />
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
