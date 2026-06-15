"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CandlestickData,
  HistogramData,
  IChartApi,
  LineData,
  MouseEventParams,
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
 *
 * J-76 (per-bar hover detail box): on crosshair move the chart surfaces a tracking detail box (mirroring
 * the `index-regime-chart.tsx` `subscribeCrosshairMove` tooltip) showing the hovered bar's `yyyy-MM-dd`
 * date (shared `formatIsoDate`, J-42), OHLC, volume, % change (a display derivation of the bar's close vs
 * the previous bar's close — presentation math over two already-served closes, like the index tooltip,
 * NOT a stored canonical value), and each rendered moving-average value (read from the SAME server `ma`
 * arrays the chart plots — single source of truth, NO extra request, NO recompute). A forward (post-as-of)
 * bar is LABELLED "after as-of (display only)" and stays visualization-only (J-20 — never an as-of signal).
 * An absent MA at the warm-up edge shows honestly as "NA", never a fabricated number. Leaving the chart
 * hides the box. The box is `pointer-events-none` and pinned to the corner so it never obscures the as-of
 * marker / forward divider (J-20) or the regime bands (J-45).
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

/** J-76: the hovered-bar detail box. Every field is read from the already-served bars / MA arrays; the
 *  % change is a display derivation of two served closes (presentation math, not a stored value). */
interface HoverDetail {
  date: string; // ISO yyyy-MM-dd
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  pctChange: number | null; // (close − prevClose) / prevClose · 100; null at the first bar
  mas: { period: string; value: number | null }[]; // each rendered MA at this bar; null = NA (warm-up edge)
  isForward: boolean; // J-20: this bar is dated after the as-of D (display-only forward region)
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
  // J-76: the hovered-bar detail box (null = no hover / off-chart). Tracks the crosshair like the
  // index-regime-chart tooltip; cleared on leave so the box disappears off the chart.
  const [hover, setHover] = useState<HoverDetail | null>(null);
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

  // J-76: ISO-date → bar index, so the crosshair time resolves the hovered bar (and its previous bar's
  // close for the % change). One pass over the already-served bars — no fetch, no recompute.
  const indexByDate = useMemo(() => {
    const map = new Map<string, number>();
    bars.forEach((bar, i) => map.set(bar.date, i));
    return map;
  }, [bars]);

  // J-76: build the detail box for the bar at `idx` from the SAME already-served arrays the chart plots
  // (OHLCV from `bars`, each MA value from the server `ma` series at the same index). The % change is a
  // display derivation of this close vs the previous bar's close (presentation math over two served
  // values — not a stored canonical value); NA at the first bar where there is no prior close. An absent
  // MA at the warm-up edge is reported honestly as null → "NA", never fabricated.
  const buildHover = useCallback(
    (idx: number): HoverDetail | null => {
      const bar = bars[idx];
      if (!bar) return null;
      const prevClose = idx > 0 ? bars[idx - 1].close : null;
      const pctChange =
        prevClose != null && prevClose !== 0 ? ((bar.close - prevClose) / prevClose) * 100 : null;
      const mas = periods.map((period) => {
        const value = ma[period]?.[idx];
        return { period, value: value == null ? null : value };
      });
      return {
        date: bar.date,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume,
        pctChange,
        mas,
        isForward: bar.is_forward === true,
      };
    },
    [bars, ma, periods],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container || bars.length === 0) return;

    let chart: IChartApi | undefined;
    let disposed = false;
    let crosshairHandler: ((param: MouseEventParams<Time>) => void) | undefined;

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

      // J-76: per-bar detail box. On crosshair move, resolve the hovered ISO date → bar index and surface
      // that bar's OHLCV / % change / MA values (read from the already-served arrays, NO recompute). Off
      // the data (no `time`/`point`) clears the box so it disappears when the cursor leaves the chart.
      crosshairHandler = (param: MouseEventParams<Time>) => {
        if (!param.time || param.point === undefined) {
          setHover(null);
          return;
        }
        const idx = indexByDate.get(isoFromTime(param.time));
        setHover(idx === undefined ? null : buildHover(idx));
      };
      chart.subscribeCrosshairMove(crosshairHandler);

      chart.timeScale().fitContent();
    })();

    return () => {
      disposed = true;
      if (chart && crosshairHandler) chart.unsubscribeCrosshairMove(crosshairHandler);
      chart?.remove();
      setHover(null);
    };
  }, [bars, ma, periods, hasForward, asofDate, hasBands, bandPoints, indexByDate, buildHover]);

  return (
    <div className="space-y-3">
      <div className="relative">
        <div ref={containerRef} className="h-80 w-full" />
        {hover ? <BarTooltip detail={hover} periods={periods} /> : null}
      </div>
      <ChartLegend periods={periods} hasForward={hasForward} asofDate={asofDate} hasBands={hasBands} />
    </div>
  );
}

/** J-76 — the per-bar hover detail box: the bar's `yyyy-MM-dd` date, OHLC, volume, % change, and each
 *  rendered MA value. A forward (post-as-of) bar is labelled "after as-of (display only)" (J-20). Pinned
 *  to the top-left corner and `pointer-events-none` so it never obscures the as-of marker / forward divider
 *  (J-20, drawn near the top-right) or the regime bands (J-45). All values re-format already-served data;
 *  an absent MA renders "NA", never a fabricated number. */
function BarTooltip({ detail, periods }: { detail: HoverDetail; periods: string[] }) {
  const fmt = (n: number) => n.toFixed(2);
  const fmtVol = (n: number) => Math.round(n).toLocaleString("en-US");
  return (
    <div
      className="pointer-events-none absolute left-3 top-3 z-10 min-w-48 rounded-md border border-border-strong bg-surface-2/95 p-3 text-xs shadow-lg backdrop-blur-sm"
      role="status"
      data-testid="price-chart-hover"
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="num font-medium text-text" data-testid="price-chart-hover-date">
          {formatIsoDate(detail.date)}
        </span>
        {detail.isForward ? (
          <span
            className="rounded-sm border border-warn/40 px-1.5 py-0.5 text-[10px] font-medium text-warn"
            data-testid="price-chart-hover-forward"
          >
            after as-of (display only)
          </span>
        ) : null}
      </div>
      <ul className="space-y-1">
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">Open</span>
          <span className="num text-text">{fmt(detail.open)}</span>
        </li>
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">High</span>
          <span className="num text-text">{fmt(detail.high)}</span>
        </li>
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">Low</span>
          <span className="num text-text">{fmt(detail.low)}</span>
        </li>
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">Close</span>
          <span className="num text-text">{fmt(detail.close)}</span>
        </li>
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">% chg</span>
          {detail.pctChange === null ? (
            <span className="num text-text-faint">NA</span>
          ) : (
            <span className={`num ${detail.pctChange >= 0 ? "text-pos" : "text-neg"}`}>
              {detail.pctChange >= 0 ? "+" : ""}
              {fmt(detail.pctChange)}%
            </span>
          )}
        </li>
        <li className="flex items-center justify-between gap-4">
          <span className="text-text-muted">Volume</span>
          <span className="num text-text">{fmtVol(detail.volume)}</span>
        </li>
      </ul>
      {periods.length > 0 ? (
        <ul className="mt-2 space-y-1 border-t border-border pt-2">
          {detail.mas.map(({ period, value }, index) => (
            <li key={period} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5 text-text-muted">
                <LegendDot varName={maColorVar(index)} />
                <span className="num">{period}</span>-DMA
              </span>
              {value === null ? (
                <span className="num text-text-faint">NA</span>
              ) : (
                <span className="num text-text">{fmt(value)}</span>
              )}
            </li>
          ))}
        </ul>
      ) : null}
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
