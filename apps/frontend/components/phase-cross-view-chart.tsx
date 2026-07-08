"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  IChartApi,
  ISeriesApi,
  LineData,
  MouseEventParams,
  Time,
} from "lightweight-charts";

import { AsOfMarkerPrimitive } from "@/components/asof-marker-primitive";
import { PhaseBandPrimitive } from "@/components/phase-band-primitive";
import { RegimeBandPrimitive } from "@/components/regime-band-primitive";
import { formatIsoDate } from "@/lib/dates";
import { familyColor, familyLabel, RISK_FAMILIES } from "@/lib/regime";
import { PHASE_POSTURES, phaseColor, postureColor, postureLabel } from "@/lib/phase";
import type { IndexSeries, MarketPhaseTimelinePoint, RegimePoint } from "@/lib/api";

/**
 * J-97 Dashboard two-pane synced cross-view. ONE `lightweight-charts` chart with TWO panes that share ONE
 * time scale — so zoom/pan/scroll on EITHER pane re-ranges BOTH to the same window (synchronization is
 * inherent in the single time scale; it is a VIEW TRANSFORM, never a second date state — J-18/J-97).
 *
 *   - Pane 0 (top): the same normalized-% index lines + stored-regime background bands + as-of marker as
 *     the J-44/J-49 "Major indexes & regime" card (unchanged lens).
 *   - Pane 1 (bottom): the SAME normalized-% index lines under PHASE-coloured bands, plus a 0–100 severity
 *     line and (iter-44, J-102) a ZERO-CENTERED severity-velocity line (replacing the retired P(bear) line)
 *     — every series read from the SAME single served full-history market-phase series
 *     (`GET /api/market-phase?full=true`). iter-44 (J-101b): that full series spans the FULL stored history
 *     independent of the as-of, so the phase bands span the full history (like the top regime pane). The
 *     bottom pane carries the SAME as-of marker the top pane uses.
 *
 * It RE-FORMATS server values only — NO client-side return / severity / probability math. The phase bands
 * read the served phase label per date via the shared `lib/phase` mapping (the SAME the Market-Phase card
 * timeline uses — coherence). Post-as-of points render display-only behind the as-of marker (J-49).
 *
 * iter-22 (J-14): this pane plots the SAME `series` as the J-44 card, so its palette was extended
 * identically (5 -> 10 slots; see the `--chart-*` token comment in globals.css) to avoid the same
 * color-collision the deep index/macro benchmarks would otherwise cause once more than 5 lines render
 * at once. The legend + tooltip also show each series' honest data vendor (omitted when null).
 */

// Palette tokens for the index lines, cycled (one source: globals.css vars). Same order as the J-44 card.
const LINE_PALETTE_VARS = [
  "--accent", "--pos", "--warn", "--neg", "--text-muted",
  "--snapshot", "--chart-orange", "--chart-lime", "--chart-blue", "--chart-pink",
] as const;

function lineColorVar(index: number): string {
  return LINE_PALETTE_VARS[index % LINE_PALETTE_VARS.length];
}

function isoFromTime(time: Time): string {
  if (typeof time === "string") return time;
  if (typeof time === "number") return new Date(time * 1000).toISOString().slice(0, 10);
  const { year, month, day } = time as { year: number; month: number; day: number };
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${year}-${pad(month)}-${pad(day)}`;
}

// dedicated overlay price-scale ids for the bottom pane's severity (0–100) + severity-velocity (zero-
// centered) lines, so they don't distort the index %-scale they share the pane with. iter-44 (J-102): the
// retired P(bear) overlay scale slot is reused for the zero-centered severity-velocity line.
const SEVERITY_SCALE_ID = "phase-severity";
const VELOCITY_SCALE_ID = "phase-velocity";

interface CrossTooltip {
  date: string;
  values: { symbol: string; pct: number; color: string; vendor: string | null }[];
  phase: string | null;
  severity: number | null;
  pBear: number | null;
  // iter-44 (J-102): the served severity-velocity for the hovered date (positive = worsening; NULL = NA at
  // the warm-up head) + the stored regime label/score (read VERBATIM from the already-fetched regime points
  // — Single source of truth; the frontend computes no velocity / regime / probability).
  severityVelocity: number | null;
  regimeLabel: string | null;
  regimeScore: number | null;
}

export function PhaseCrossViewChart({
  series,
  regimePoints,
  timeline,
  asofDate,
  isHistorical = false,
}: {
  // the normalized-% index lines (the SAME server-computed `series` the J-44 card plots; full history).
  series: IndexSeries[];
  // the stored regime points for pane 0's bands (J-44/J-49 — unchanged lens).
  regimePoints: RegimePoint[];
  // the served full-history causal phase timeline for pane 1 (phase bands + severity + filtered P(bear)).
  timeline: MarketPhaseTimelinePoint[];
  // the resolved as-of D — the marker position on BOTH panes while historical (J-49 display-only past D).
  asofDate: string;
  isHistorical?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<CrossTooltip | null>(null);

  const colorVarBySymbol = useMemo(() => {
    const map = new Map<string, string>();
    series.forEach((s, index) => map.set(s.symbol, lineColorVar(index)));
    return map;
  }, [series]);

  // phase-timeline lookup by ISO date for the tooltip (served label/severity/p_bear/severity_velocity read
  // verbatim — never recomputed).
  const phaseByDate = useMemo(() => {
    const map = new Map<string, MarketPhaseTimelinePoint>();
    timeline.forEach((point) => map.set(point.date, point));
    return map;
  }, [timeline]);

  // iter-44 (J-102): the stored regime label + 0–100 score per ISO date, for the enriched tooltip — read
  // VERBATIM from the already-fetched `/api/regime-history` points (the SAME series the top pane's bands
  // use; Single source of truth, Scores must be explainable). The frontend computes no regime value.
  const regimeByDate = useMemo(() => {
    const map = new Map<string, RegimePoint>();
    regimePoints.forEach((point) => map.set(point.date, point));
    return map;
  }, [regimePoints]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || series.length === 0) return;

    let chart: IChartApi | undefined;
    let disposed = false;
    let crosshairHandler: ((param: MouseEventParams<Time>) => void) | undefined;

    void (async () => {
      const lwc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      const css = getComputedStyle(document.documentElement);
      const token = (name: string) => css.getPropertyValue(name).trim();

      chart = lwc.createChart(container, {
        autoSize: true,
        layout: {
          background: { type: lwc.ColorType.Solid, color: token("--surface") },
          textColor: token("--text-muted"),
          attributionLogo: false,
        },
        grid: {
          vertLines: { color: token("--border") },
          horzLines: { color: token("--border") },
        },
        rightPriceScale: { borderColor: token("--border-strong") },
        timeScale: {
          borderColor: token("--border-strong"),
          // iter-22 (J-14 audit fix): lightweight-charts 5.2.0 enforces a default minBarSpacing floor of
          // 0.5 px/bar. With the ~7.7k-bar 30-year deep basis (^SPX back to 1996-01-02) in a ~1,000 px
          // pane, `fitContent()` below hits that floor and can only fit the most-recent ~2k bars (~8 yr) —
          // silently hiding the committed 1996 ^SPX/^NDX/^DJI history this iteration exists to surface
          // (DoD (a): the deep benchmark line must extend before SPY's 2005 start on the default view).
          // Lowering the floor lets `fitContent()` fit the FULL window by default with no manual zoom/pan.
          // 0.02 px/bar fits ~7.7k bars in a pane as narrow as ~154 px, covering every card width down to
          // mobile (~328 px pane → 0.043 px/bar needed) with headroom for a still-deeper future basis.
          minBarSpacing: 0.02,
        },
        crosshair: { mode: lwc.CrosshairMode.Normal },
        localization: {
          priceFormatter: (price: number) => `${price.toFixed(1)}%`,
          timeFormatter: (time: Time) => formatIsoDate(isoFromTime(time)),
        },
      });

      // ---- Pane 0 (top): index % lines + stored-regime bands + as-of marker (the J-44/J-49 lens). ----
      const topLineSeries: ISeriesApi<"Line">[] = [];
      series.forEach((s, index) => {
        const line = chart!.addSeries(
          lwc.LineSeries,
          {
            color: token(lineColorVar(index)),
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          0, // paneIndex 0
        );
        line.setData(s.points.map((p): LineData<Time> => ({ time: p.date as Time, value: p.pct })));
        topLineSeries.push(line);
      });
      if (regimePoints.length > 0 && topLineSeries[0]) {
        const regimeBand = new RegimeBandPrimitive();
        topLineSeries[0].attachPrimitive(regimeBand);
        regimeBand.setData(regimePoints, null); // full history (no clamp); marker shows D
      }
      if (isHistorical && topLineSeries[0]) {
        const topMarker = new AsOfMarkerPrimitive();
        topLineSeries[0].attachPrimitive(topMarker);
        topMarker.setData(asofDate, token("--warn"), `as-of ${formatIsoDate(asofDate)}`);
      }

      // ---- Pane 1 (bottom): SAME index % lines + PHASE bands + severity (0–100) + P(bear) (0–1). ----
      const bottomLineSeries: ISeriesApi<"Line">[] = [];
      series.forEach((s, index) => {
        const line = chart!.addSeries(
          lwc.LineSeries,
          {
            color: token(lineColorVar(index)),
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          1, // paneIndex 1 — shares the ONE time scale (synchronized zoom)
        );
        line.setData(s.points.map((p): LineData<Time> => ({ time: p.date as Time, value: p.pct })));
        bottomLineSeries.push(line);
      });

      // phase bands behind the bottom lines (shared mapping with the Market-Phase card — coherence).
      if (timeline.length > 0 && bottomLineSeries[0]) {
        const phaseBand = new PhaseBandPrimitive();
        bottomLineSeries[0].attachPrimitive(phaseBand);
        phaseBand.setData(timeline, null); // full history; the marker shows D (post-D display-only)
      }

      // the 0–100 severity line on its own overlay scale (so it doesn't distort the % index scale).
      if (timeline.length > 0) {
        const severitySeries = chart!.addSeries(
          lwc.LineSeries,
          {
            color: token("--neg"),
            lineWidth: 1,
            priceScaleId: SEVERITY_SCALE_ID,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          1,
        );
        severitySeries.setData(
          timeline.map((pt): LineData<Time> => ({ time: pt.date as Time, value: pt.severity })),
        );
        // iter-44 (J-102): the ZERO-CENTERED severity-velocity line (severity-points per snapshot; positive =
        // worsening) on its OWN overlay scale (the retired P(bear) scale slot), so the index % lines stay
        // undistorted. NA (null) warm-up points are dropped so no fabricated slope is drawn. A horizontal 0
        // reference line marks the worsening/easing boundary. The plotted P(bear) line is REMOVED (J-102 —
        // it was visually low-signal); its value stays in the tooltip below.
        const velocitySeries = chart!.addSeries(
          lwc.LineSeries,
          {
            color: token("--accent"),
            lineWidth: 1,
            priceScaleId: VELOCITY_SCALE_ID,
            priceLineVisible: false,
            lastValueVisible: false,
          },
          1,
        );
        velocitySeries.setData(
          timeline
            .filter((pt): pt is MarketPhaseTimelinePoint & { severity_velocity: number } =>
              typeof pt.severity_velocity === "number",
            )
            .map((pt): LineData<Time> => ({ time: pt.date as Time, value: pt.severity_velocity })),
        );
        // the 0 reference on the velocity scale (the worsening/easing boundary — a zero-centered line).
        velocitySeries.createPriceLine({
          price: 0,
          color: token("--text-faint"),
          lineWidth: 1,
          lineStyle: lwc.LineStyle.Dashed,
          axisLabelVisible: false,
          title: "0",
        });
        // keep the two overlay scales out of the way of the % index lines (margins, invisible borders). The
        // velocity scale is zero-centered: equal top/bottom margins keep 0 near the pane's vertical middle.
        severitySeries.priceScale().applyOptions({
          scaleMargins: { top: 0.1, bottom: 0.1 },
          visible: false,
        });
        velocitySeries.priceScale().applyOptions({
          scaleMargins: { top: 0.1, bottom: 0.1 },
          visible: false,
        });
      }

      // the SAME as-of marker on the bottom pane (J-97: the bottom pane carries the as-of marker).
      if (isHistorical && bottomLineSeries[0]) {
        const bottomMarker = new AsOfMarkerPrimitive();
        bottomLineSeries[0].attachPrimitive(bottomMarker);
        bottomMarker.setData(asofDate, token("--warn"), `as-of ${formatIsoDate(asofDate)}`);
      }

      // Tooltip: date + each index % (from the bottom series at that time) + the served phase/severity/
      // P(bear) for that date (read verbatim — never recomputed).
      crosshairHandler = (param: MouseEventParams<Time>) => {
        if (!param.time || param.point === undefined) {
          setTooltip(null);
          return;
        }
        const date = isoFromTime(param.time);
        const values: CrossTooltip["values"] = [];
        series.forEach((s, index) => {
          const data = param.seriesData.get(bottomLineSeries[index]) as { value?: number } | undefined;
          if (data && typeof data.value === "number") {
            values.push({
              symbol: s.symbol,
              pct: data.value,
              color: token(lineColorVar(index)),
              vendor: s.vendor,
            });
          }
        });
        const pt = phaseByDate.get(date) ?? null;
        const regime = regimeByDate.get(date) ?? null;
        setTooltip({
          date,
          values,
          phase: pt?.phase ?? null,
          severity: pt?.severity ?? null,
          pBear: pt?.p_bear ?? null,
          // iter-44 (J-102): the served severity-velocity (NA at the warm-up head) + the stored regime
          // label/score, all read VERBATIM (never recomputed).
          severityVelocity: pt?.severity_velocity ?? null,
          regimeLabel: regime?.label ?? null,
          regimeScore: regime?.score ?? null,
        });
      };
      chart.subscribeCrosshairMove(crosshairHandler);

      chart.timeScale().fitContent();
    })();

    return () => {
      disposed = true;
      if (chart && crosshairHandler) chart.unsubscribeCrosshairMove(crosshairHandler);
      chart?.remove();
      setTooltip(null);
    };
  }, [series, regimePoints, timeline, asofDate, isHistorical, phaseByDate, regimeByDate]);

  return (
    <div className="space-y-3">
      <div className="relative">
        <div ref={containerRef} className="h-[28rem] w-full" data-testid="phase-cross-view-chart" />
        {tooltip ? <CrossTooltipBox tooltip={tooltip} /> : null}
      </div>
      <CrossLegend
        series={series}
        colorVarBySymbol={colorVarBySymbol}
        hasRegimeBands={regimePoints.length > 0}
        hasPhaseBands={timeline.length > 0}
      />
    </div>
  );
}

/** The hover tooltip: the ISO date, each index's %, and the served phase + 0–100 severity + filtered
 *  P(bear) + iter-44 (J-102) severity-velocity + the stored market-regime label/score for that date (all
 *  read verbatim — never recomputed). */
function CrossTooltipBox({ tooltip }: { tooltip: CrossTooltip }) {
  return (
    <div
      className="pointer-events-none absolute right-3 top-3 z-10 min-w-48 rounded-md border border-border-strong bg-surface-2/95 p-3 text-xs shadow-lg backdrop-blur-sm"
      role="status"
    >
      <p className="num mb-2 font-medium text-text">{formatIsoDate(tooltip.date)}</p>
      <ul className="space-y-1">
        {tooltip.values.map((v) => (
          <li key={v.symbol} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-text-muted">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: v.color }} aria-hidden />
              {v.symbol}
              {v.vendor ? <span className="text-text-faint">· {v.vendor}</span> : null}
            </span>
            <span className="num text-text">{v.pct >= 0 ? "+" : ""}{v.pct.toFixed(2)}%</span>
          </li>
        ))}
      </ul>
      {/* iter-44 (J-102): the stored market-regime label + 0–100 score (read verbatim from the regime-history
          points — Single source of truth; Scores must be explainable). */}
      {tooltip.regimeLabel ? (
        <div className="mt-2 space-y-1 border-t border-border pt-2">
          <span className="flex items-center justify-between gap-4">
            <span className="text-text-muted">Regime</span>
            <span className="num text-text">
              {tooltip.regimeLabel}
              {tooltip.regimeScore !== null ? (
                <span className="text-text-muted"> · {tooltip.regimeScore.toFixed(0)}/100</span>
              ) : null}
            </span>
          </span>
        </div>
      ) : null}
      {tooltip.phase ? (
        <div className="mt-2 space-y-1 border-t border-border pt-2">
          <span className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-text-muted">
              <span
                className="inline-block h-2 w-2 rounded-sm"
                style={{ backgroundColor: phaseColor(tooltip.phase) }}
                aria-hidden
              />
              {tooltip.phase}
            </span>
            {tooltip.severity !== null ? (
              <span className="num text-text">sev {tooltip.severity.toFixed(0)}</span>
            ) : null}
          </span>
          {tooltip.pBear !== null ? (
            <span className="flex items-center justify-between gap-4">
              <span className="text-text-muted">P(bear)</span>
              <span className="num text-text">{tooltip.pBear.toFixed(2)}</span>
            </span>
          ) : null}
          {/* iter-44 (J-102): the served severity-velocity (positive = worsening; NA at the warm-up head). */}
          <span className="flex items-center justify-between gap-4">
            <span className="text-text-muted">Severity velocity</span>
            <span className="num text-text">
              {tooltip.severityVelocity !== null
                ? `${tooltip.severityVelocity > 0 ? "+" : ""}${tooltip.severityVelocity.toFixed(2)}`
                : "NA"}
            </span>
          </span>
        </div>
      ) : null}
    </div>
  );
}

/** Legend: one swatch per plotted index, the three regime families (top pane), the three phase postures
 *  (bottom pane bands), plus the severity + P(bear) line swatches. */
function CrossLegend({
  series,
  colorVarBySymbol,
  hasRegimeBands,
  hasPhaseBands,
}: {
  series: IndexSeries[];
  colorVarBySymbol: Map<string, string>;
  hasRegimeBands: boolean;
  hasPhaseBands: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-muted">
        {series.map((s) => (
          <span key={s.symbol} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: `var(${colorVarBySymbol.get(s.symbol)})` }}
              aria-hidden
            />
            {s.name}
            {s.vendor ? <span className="text-text-faint">({s.vendor})</span> : null}
          </span>
        ))}
        {hasRegimeBands
          ? RISK_FAMILIES.map((family) => (
              <span key={family} className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2 w-2 rounded-sm"
                  style={{ backgroundColor: familyColor(family) }}
                  aria-hidden
                />
                {familyLabel(family)} regime
              </span>
            ))
          : null}
      </div>
      {hasPhaseBands ? (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-faint">
          <span className="uppercase tracking-wide">Phase pane:</span>
          {PHASE_POSTURES.map((posture) => (
            <span key={posture} className="flex items-center gap-1.5">
              <span
                className="inline-block h-2 w-2 rounded-sm"
                style={{ backgroundColor: postureColor(posture) }}
                aria-hidden
              />
              {postureLabel(posture)} phase
            </span>
          ))}
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-3 rounded-sm" style={{ backgroundColor: "var(--neg)" }} aria-hidden />
            Severity (0–100)
          </span>
          {/* iter-44 (J-102): the zero-centered severity-velocity line replaces the retired P(bear) line. */}
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-3 rounded-sm" style={{ backgroundColor: "var(--accent)" }} aria-hidden />
            Severity velocity (0-centered; + = worsening)
          </span>
        </div>
      ) : null}
    </div>
  );
}
