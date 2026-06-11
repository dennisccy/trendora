"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  IChartApi,
  ISeriesApi,
  LineData,
  MouseEventParams,
  Time,
} from "lightweight-charts";

import { RegimeBandPrimitive } from "@/components/regime-band-primitive";
import { formatIsoDate } from "@/lib/dates";
import { familyColor, familyLabel, regimeFamily, RISK_FAMILIES } from "@/lib/regime";
import type { IndexSeries, RegimePoint } from "@/lib/api";

/**
 * The J-44 "Major indexes & regime" chart body: normalized-% index lines over soft market-regime
 * background bands, with a hover tooltip showing the `yyyy-MM-dd` date, each index's % value, and the
 * exact stored regime label + score for that date.
 *
 * It RE-FORMATS server values only: the % lines are the server-computed `series` (no client return math),
 * and the bands + tooltip read the stored regime points via the SAME `lib/regime` mapping the stock-detail
 * chart uses (coherence: same date ⇒ same band color everywhere). It computes no regime and no return.
 *
 * Line colors come from the DESIGN SYSTEM palette tokens (globals.css), cycled per series; the legend
 * mirrors that order so a line and its legend swatch always match.
 */

// Palette tokens for the index lines, cycled (one source: globals.css vars).
const LINE_PALETTE_VARS = ["--accent", "--pos", "--warn", "--neg", "--text-muted"] as const;

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

interface TooltipState {
  date: string; // ISO yyyy-MM-dd
  values: { symbol: string; pct: number; color: string }[];
  regimeLabel: string | null;
  regimeScore: number | null;
}

export function IndexRegimeChart({
  series,
  regimePoints,
  asofDate,
}: {
  series: IndexSeries[];
  regimePoints: RegimePoint[];
  asofDate: string; // the resolved as-of D — bands never paint past it (no-lookahead)
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  // Stable color per symbol so the line, legend, and tooltip agree.
  const colorVarBySymbol = useMemo(() => {
    const map = new Map<string, string>();
    series.forEach((s, index) => map.set(s.symbol, lineColorVar(index)));
    return map;
  }, [series]);

  // Regime lookup by ISO date for the tooltip (stored label/score read verbatim — never recomputed).
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
        timeScale: { borderColor: token("--border-strong") },
        crosshair: { mode: lwc.CrosshairMode.Normal },
        localization: {
          // % price-scale formatter + ISO crosshair date (J-42: one shared formatter, no locale path).
          priceFormatter: (price: number) => `${price.toFixed(1)}%`,
          timeFormatter: (time: Time) => formatIsoDate(isoFromTime(time)),
        },
      });

      // Regime bands behind the lines — the SAME primitive + mapping as the stock-detail chart (J-45),
      // clipped at the as-of date so nothing paints in a post-as-of region (no-lookahead). Attached to
      // the FIRST line series (any series shares the same time scale).
      const lineSeries: ISeriesApi<"Line">[] = [];
      series.forEach((s, index) => {
        const line = chart!.addSeries(lwc.LineSeries, {
          color: token(lineColorVar(index)),
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        line.setData(
          s.points.map((p): LineData<Time> => ({ time: p.date as Time, value: p.pct })),
        );
        lineSeries.push(line);
      });

      if (regimePoints.length > 0 && lineSeries[0]) {
        const bandPrimitive = new RegimeBandPrimitive();
        lineSeries[0].attachPrimitive(bandPrimitive);
        bandPrimitive.setData(
          regimePoints.filter((point) => point.date <= asofDate),
          asofDate,
        );
      }

      // Tooltip: on crosshair move, surface the date, each index % (from the series data at that time),
      // and the stored regime label + score for that date (read verbatim from the regime map).
      crosshairHandler = (param: MouseEventParams<Time>) => {
        if (!param.time || param.point === undefined) {
          setTooltip(null);
          return;
        }
        const date = isoFromTime(param.time);
        const values: TooltipState["values"] = [];
        series.forEach((s, index) => {
          const data = param.seriesData.get(lineSeries[index]) as { value?: number } | undefined;
          if (data && typeof data.value === "number") {
            values.push({
              symbol: s.symbol,
              pct: data.value,
              color: token(lineColorVar(index)),
            });
          }
        });
        const regime = regimeByDate.get(date) ?? null;
        setTooltip({
          date,
          values,
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
  }, [series, regimePoints, asofDate, regimeByDate]);

  return (
    <div className="space-y-3">
      <div className="relative">
        <div ref={containerRef} className="h-80 w-full" />
        {tooltip ? <IndexTooltip tooltip={tooltip} /> : null}
      </div>
      <IndexLegend series={series} colorVarBySymbol={colorVarBySymbol} hasBands={regimePoints.length > 0} />
    </div>
  );
}

/** The hover tooltip: the ISO date, each index's % value, and the exact stored regime label + score. */
function IndexTooltip({ tooltip }: { tooltip: TooltipState }) {
  return (
    <div
      className="pointer-events-none absolute right-3 top-3 z-10 min-w-44 rounded-md border border-border-strong bg-surface-2/95 p-3 text-xs shadow-lg backdrop-blur-sm"
      role="status"
    >
      <p className="num mb-2 font-medium text-text">{formatIsoDate(tooltip.date)}</p>
      <ul className="space-y-1">
        {tooltip.values.map((v) => (
          <li key={v.symbol} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-text-muted">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: v.color }} aria-hidden />
              {v.symbol}
            </span>
            <span className="num text-text">{v.pct >= 0 ? "+" : ""}{v.pct.toFixed(2)}%</span>
          </li>
        ))}
      </ul>
      {tooltip.regimeLabel ? (
        <div className="mt-2 border-t border-border pt-2">
          <span className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-text-muted">
              <span
                className="inline-block h-2 w-2 rounded-sm"
                style={{ backgroundColor: familyColor(regimeFamily(tooltip.regimeLabel)) }}
                aria-hidden
              />
              {tooltip.regimeLabel}
            </span>
            {tooltip.regimeScore !== null ? (
              <span className="num text-text">{tooltip.regimeScore.toFixed(1)}</span>
            ) : null}
          </span>
        </div>
      ) : null}
    </div>
  );
}

/** Legend: one swatch per plotted index (matching the chart line colors) + the three regime families. */
function IndexLegend({
  series,
  colorVarBySymbol,
  hasBands,
}: {
  series: IndexSeries[];
  colorVarBySymbol: Map<string, string>;
  hasBands: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-muted">
      {series.map((s) => (
        <span key={s.symbol} className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: `var(${colorVarBySymbol.get(s.symbol)})` }}
            aria-hidden
          />
          {s.name}
        </span>
      ))}
      {hasBands
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
  );
}
