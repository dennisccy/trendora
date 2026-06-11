"use client";

import { useEffect, useMemo, useRef } from "react";
import type {
  CandlestickData,
  HistogramData,
  IChartApi,
  LineData,
  SeriesMarker,
  Time,
} from "lightweight-charts";

import type { PriceBar, RegimePoint } from "@/lib/api";
import { formatIsoDate } from "@/lib/dates";
import { RegimeBandPrimitive } from "@/components/regime-band-primitive";
import { familyColor, familyLabel, RISK_FAMILIES } from "@/lib/regime";

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
 *
 * J-20 (display-only forward extension): when bars carry `is_forward` (the `through=latest` chart at
 * a historical as-of D), the post-D candles + volume are drawn in a MUTED palette token and an as-of
 * boundary marker is placed at D, so the forward region reads unmistakably as "after the as-of date /
 * display only" — it is visualization only and never a signal (the scores stay on the <= D snapshot).
 */

// Palette tokens for the MA overlays, in shortest→longest order (one source: globals.css vars).
const MA_PALETTE_VARS = ["--accent", "--warn", "--text-muted", "--text-faint"] as const;

// J-20: the post-as-of (forward) region is rendered DISPLAY-ONLY in a muted palette so it reads as
// "after the as-of date", never as a signal. One source: globals.css CSS vars (no ad-hoc hex).
const FORWARD_CANDLE_VAR = "--text-faint";
const FORWARD_VOLUME_VAR = "--border-strong";
const ASOF_MARKER_VAR = "--warn";

function maColorVar(index: number): string {
  return MA_PALETTE_VARS[index % MA_PALETTE_VARS.length];
}

/**
 * Normalise a Lightweight-Charts `Time` to an ISO `yyyy-MM-dd` string for the shared formatter.
 * Our series uses string business-day times (the backend's ISO `bar.date`), so `time` is normally that
 * exact string; the BusinessDay-object and UNIX-timestamp shapes are handled defensively so the
 * crosshair date is always ISO and never a locale-formatted value.
 */
function isoFromTime(time: Time): string {
  if (typeof time === "string") return time;
  if (typeof time === "number") return new Date(time * 1000).toISOString().slice(0, 10);
  // BusinessDay object { year, month, day } — pad to yyyy-MM-dd.
  const { year, month, day } = time as { year: number; month: number; day: number };
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${year}-${pad(month)}-${pad(day)}`;
}

export function PriceChart({
  bars,
  ma,
  asofDate,
  regimePoints,
  regimeEnabled = false,
}: {
  bars: PriceBar[];
  ma: Record<string, (number | null)[]>;
  asofDate?: string; // the resolved as-of D — labels the forward-region boundary marker (J-20)
  // J-45: the stored regime-history points (date <= as-of) for the soft background bands. The SAME
  // stored values + the SAME lib/regime color mapping as the dashboard card (coherence). Undefined /
  // empty ⇒ no bands. Bounded to <= as-of by the endpoint, so the forward region stays band-free (J-20).
  regimePoints?: RegimePoint[];
  regimeEnabled?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  // Only the points dated <= the as-of are eligible for bands; the post-as-of forward region never gets
  // a band (J-20). The endpoint already bounds them, but we re-assert it here as a defensive clip.
  const bandPoints = useMemo(() => {
    if (!regimeEnabled || !regimePoints || regimePoints.length === 0) return [];
    if (!asofDate) return regimePoints;
    return regimePoints.filter((point) => point.date <= asofDate);
  }, [regimeEnabled, regimePoints, asofDate]);
  const hasBands = bandPoints.length > 0;
  // MA periods shortest→longest (numeric), so overlay colours and the legend stay aligned.
  const periods = useMemo(
    () => Object.keys(ma).sort((a, b) => Number(a) - Number(b)),
    [ma],
  );
  // J-20: a forward region exists only when the payload marked post-D bars (the historical-as-of
  // through=latest chart). At the latest as-of there are none, so the chart is visually unchanged.
  const hasForward = useMemo(() => bars.some((bar) => bar.is_forward), [bars]);

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
        // J-42: the crosshair/tooltip DATE is a displayed calendar date — render it `yyyy-MM-dd`
        // through the one shared formatter (no locale-dependent path). The compact axis TICK labels
        // stay the library default (abbreviated scale marks, not displayed dates — per J-42 acceptance).
        localization: { timeFormatter: (time: Time) => formatIsoDate(isoFromTime(time)) },
      });

      const forwardCandle = token(FORWARD_CANDLE_VAR);
      const candles = chart.addSeries(lwc.CandlestickSeries, {
        upColor: token("--pos"),
        downColor: token("--neg"),
        wickUpColor: token("--pos"),
        wickDownColor: token("--neg"),
        borderVisible: false,
      });

      // J-45: soft regime background bands behind price. The primitive reads the SAME stored regime
      // points + lib/regime mapping as the dashboard card (coherence) and clips at the as-of date so the
      // forward region stays band-free (J-20). Attached to the candle series; disposed with the chart.
      if (hasBands) {
        const bandPrimitive = new RegimeBandPrimitive();
        candles.attachPrimitive(bandPrimitive);
        bandPrimitive.setData(bandPoints, asofDate ?? null);
      }
      candles.setData(
        bars.map((bar): CandlestickData<Time> => {
          const point: CandlestickData<Time> = {
            time: bar.date as Time,
            open: bar.open,
            high: bar.high,
            low: bar.low,
            close: bar.close,
          };
          // display-only forward bar: mute body + wick so it reads as "after the as-of date"
          if (bar.is_forward) {
            point.color = forwardCandle;
            point.wickColor = forwardCandle;
            point.borderColor = forwardCandle;
          }
          return point;
        }),
      );

      // J-20: place an as-of boundary marker at D (the last <= D bar) so the forward region is
      // unmistakable. Only when a forward region exists — the latest-as-of chart stays unmarked.
      if (hasForward) {
        const boundary = [...bars].reverse().find((bar) => !bar.is_forward);
        if (boundary) {
          const markers: SeriesMarker<Time>[] = [
            {
              time: boundary.date as Time,
              position: "aboveBar",
              color: token(ASOF_MARKER_VAR),
              shape: "arrowDown",
              text: asofDate ? `as-of ${asofDate}` : "as-of",
            },
          ];
          lwc.createSeriesMarkers(candles, markers);
        }
      }

      // volume as a muted histogram pinned to the bottom of the pane (its own price scale); the
      // forward region's bars are muted a shade further so they recede behind the <= D series (J-20)
      const forwardVolume = token(FORWARD_VOLUME_VAR);
      const volume = chart.addSeries(lwc.HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "volume",
        color: token("--text-faint"),
      });
      chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
      volume.setData(
        bars.map((bar): HistogramData<Time> => {
          const point: HistogramData<Time> = { time: bar.date as Time, value: bar.volume };
          if (bar.is_forward) point.color = forwardVolume;
          return point;
        }),
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
  }, [bars, ma, periods, hasForward, asofDate, hasBands, bandPoints]);

  return (
    <div className="space-y-3">
      <div ref={containerRef} className="h-80 w-full" />
      <ChartLegend periods={periods} hasForward={hasForward} asofDate={asofDate} hasBands={hasBands} />
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
 *  both read the same CSS var). Candle up/down, the MA overlays, volume, and — when a forward region
 *  is shown (J-20) — the muted "after as-of (display only)" swatch that labels the post-D bars. */
function ChartLegend({
  periods,
  hasForward,
  asofDate,
  hasBands,
}: {
  periods: string[];
  hasForward: boolean;
  asofDate?: string;
  hasBands?: boolean;
}) {
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
      {hasForward ? (
        <span className="flex items-center gap-1.5 text-text-faint">
          <LegendDot varName={FORWARD_CANDLE_VAR} />
          Forward — after as-of{asofDate ? ` ${asofDate}` : ""} (display only)
        </span>
      ) : null}
    </div>
  );
}
