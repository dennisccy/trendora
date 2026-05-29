"use client";

import { useEffect, useMemo, useRef } from "react";
import type {
  CandlestickData,
  HistogramData,
  IChartApi,
  LineData,
  Time,
} from "lightweight-charts";

import type { PriceBar } from "@/lib/api";

/**
 * Client-only price chart (Lightweight-Charts, MIT-style permissive / Apache-2.0, no key, no
 * runtime network callout). It RE-FORMATS server values only: candles come from `bars`, and each
 * moving-average overlay is plotted from the server `ma[period]` series — the chart NEVER computes
 * a moving average from the close array (single source of truth). The library touches `document`,
 * so it is dynamically imported inside an effect (SSR-safe) and disposed on unmount.
 *
 * Colours are read at runtime from the SAME CSS palette tokens the rest of the UI uses
 * (app/globals.css) — no arbitrary hex. MA overlays cycle through accent → warn → muted → faint,
 * so the shortest MA is brightest and the longest faintest; the legend mirrors the order.
 */

// Palette tokens for the MA overlays, in shortest→longest order (one source: globals.css vars).
const MA_PALETTE_VARS = ["--accent", "--warn", "--text-muted", "--text-faint"] as const;

function maColorVar(index: number): string {
  return MA_PALETTE_VARS[index % MA_PALETTE_VARS.length];
}

export function PriceChart({
  bars,
  ma,
}: {
  bars: PriceBar[];
  ma: Record<string, (number | null)[]>;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  // MA periods shortest→longest (numeric), so overlay colours and the legend stay aligned.
  const periods = useMemo(
    () => Object.keys(ma).sort((a, b) => Number(a) - Number(b)),
    [ma],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container || bars.length === 0) return;

    let chart: IChartApi | undefined;
    let disposed = false;

    void (async () => {
      const lwc = await import("lightweight-charts");
      if (disposed || !containerRef.current) return;

      const css = getComputedStyle(document.documentElement);
      const token = (name: string) => css.getPropertyValue(name).trim();

      chart = lwc.createChart(container, {
        autoSize: true, // tracks the container (sized by the h-80 Tailwind class) via ResizeObserver
        layout: {
          background: { type: lwc.ColorType.Solid, color: token("--surface") },
          textColor: token("--text-muted"),
          attributionLogo: false, // hide the TradingView logo overlay — keep the surface clean
        },
        grid: {
          vertLines: { color: token("--border") },
          horzLines: { color: token("--border") },
        },
        rightPriceScale: { borderColor: token("--border-strong") },
        timeScale: { borderColor: token("--border-strong") },
        crosshair: { mode: lwc.CrosshairMode.Normal },
      });

      const candles = chart.addSeries(lwc.CandlestickSeries, {
        upColor: token("--pos"),
        downColor: token("--neg"),
        wickUpColor: token("--pos"),
        wickDownColor: token("--neg"),
        borderVisible: false,
      });
      candles.setData(
        bars.map(
          (bar): CandlestickData<Time> => ({
            time: bar.date as Time,
            open: bar.open,
            high: bar.high,
            low: bar.low,
            close: bar.close,
          }),
        ),
      );

      // volume as a muted histogram pinned to the bottom of the pane (its own price scale)
      const volume = chart.addSeries(lwc.HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
        color: token("--text-faint"),
      });
      chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
      volume.setData(
        bars.map((bar): HistogramData<Time> => ({ time: bar.date as Time, value: bar.volume })),
      );

      // one line series per server MA period — plot the server values, skipping the NA warm-up gap
      periods.forEach((period, index) => {
        const series = ma[period] ?? [];
        const points: LineData<Time>[] = [];
        bars.forEach((bar, barIndex) => {
          const value = series[barIndex];
          if (value != null) points.push({ time: bar.date as Time, value });
        });
        if (points.length === 0 || !chart) return;
        const line = chart.addSeries(lwc.LineSeries, {
          color: token(maColorVar(index)),
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        line.setData(points);
      });

      chart.timeScale().fitContent();
    })();

    return () => {
      disposed = true;
      chart?.remove();
    };
  }, [bars, ma, periods]);

  return (
    <div className="space-y-3">
      <div ref={containerRef} className="h-80 w-full" />
      <ChartLegend periods={periods} />
    </div>
  );
}

function LegendDot({ varName }: { varName: string }) {
  return (
    <span
      className="inline-block h-2 w-2 rounded-full"
      style={{ backgroundColor: `var(${varName})` }}
      aria-hidden
    />
  );
}

/** Compact legend mapping each plotted series to its palette colour (matches the chart exactly:
 *  both read the same CSS var). Candle up/down, the MA overlays, and volume. */
function ChartLegend({ periods }: { periods: string[] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-text-muted">
      <span className="flex items-center gap-1.5">
        <LegendDot varName="--pos" />
        <LegendDot varName="--neg" />
        Candles (up / down)
      </span>
      {periods.map((period, index) => (
        <span key={period} className="flex items-center gap-1.5">
          <LegendDot varName={maColorVar(index)} />
          <span className="num">{period}</span>-DMA
        </span>
      ))}
      <span className="flex items-center gap-1.5">
        <LegendDot varName="--text-faint" />
        Volume
      </span>
    </div>
  );
}
