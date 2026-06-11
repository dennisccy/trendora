/**
 * Lightweight-Charts series primitive that paints soft market-regime BACKGROUND BANDS behind a chart
 * (J-44 dashboard index chart + J-45 stock-detail price chart). Both surfaces attach THIS one primitive,
 * fed by the same stored regime-history points and the same `lib/regime` color mapping, so the same date
 * shows the same band color everywhere (coherence).
 *
 * The bands are an HONEST STEP FUNCTION between snapshot dates: each stored regime point owns the
 * horizontal span from its own date up to (not including) the next stored point's date; the last point
 * extends to the right edge — but NEVER past the resolved as-of date. The primitive is given only points
 * with `date <= asOfDate`, and it clips the final band's right edge at the as-of x-coordinate, so no band
 * is ever drawn in the post-as-of forward region (J-20 / J-45: the forward region stays band-free).
 *
 * It computes NO regime — it only reads stored labels the backend served and maps them to a palette
 * color via `regimeBandFill`. Drawn on the BACKGROUND layer (`zOrder: 'bottom'`) so price/index lines and
 * the grid sit on top.
 */
import type {
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesPrimitive,
  PrimitivePaneViewZOrder,
  SeriesAttachedParameter,
  Time,
} from "lightweight-charts";

import { regimeBandFill } from "@/lib/regime";
import type { RegimePoint } from "@/lib/api";

interface BandRect {
  left: number;
  right: number;
  fill: string;
}

/** Minimal shape we need from a CanvasRenderingTarget2D — the bitmap-coordinate drawing space. */
interface BitmapTarget {
  useBitmapCoordinateSpace(
    callback: (scope: {
      context: CanvasRenderingContext2D;
      bitmapSize: { width: number; height: number };
      horizontalPixelRatio: number;
      verticalPixelRatio: number;
    }) => void,
  ): void;
}

class RegimeBandRenderer implements IPrimitivePaneRenderer {
  constructor(private readonly rects: BandRect[]) {}

  draw(): void {
    // Bands are background-only; nothing on the foreground layer.
  }

  drawBackground(target: unknown): void {
    const bitmapTarget = target as BitmapTarget;
    bitmapTarget.useBitmapCoordinateSpace(
      ({ context: ctx, bitmapSize, horizontalPixelRatio }) => {
        for (const rect of this.rects) {
          const left = Math.round(rect.left * horizontalPixelRatio);
          const right = Math.round(rect.right * horizontalPixelRatio);
          const width = right - left;
          if (width <= 0) continue;
          ctx.fillStyle = rect.fill;
          ctx.fillRect(left, 0, width, bitmapSize.height);
        }
      },
    );
  }
}

class RegimeBandPaneView implements IPrimitivePaneView {
  constructor(private readonly source: RegimeBandPrimitive) {}

  zOrder(): PrimitivePaneViewZOrder {
    return "bottom"; // behind the candles/lines and grid
  }

  renderer(): IPrimitivePaneRenderer {
    return new RegimeBandRenderer(this.source.computeRects());
  }
}

export class RegimeBandPrimitive implements ISeriesPrimitive<Time> {
  private params: SeriesAttachedParameter<Time> | null = null;
  private readonly paneView: RegimeBandPaneView;
  private points: RegimePoint[] = [];
  private asOfDate: string | null = null;

  constructor() {
    this.paneView = new RegimeBandPaneView(this);
  }

  /** Update the stored regime points + the as-of right bound, then request a redraw. Points MUST already
   *  be filtered to `date <= asOfDate` by the caller; this also clips the last band at the as-of x. */
  setData(points: RegimePoint[], asOfDate: string | null): void {
    this.points = points;
    this.asOfDate = asOfDate;
    this.params?.requestUpdate();
  }

  attached(param: SeriesAttachedParameter<Time>): void {
    this.params = param;
  }

  detached(): void {
    this.params = null;
  }

  updateAllViews(): void {
    // Rects are recomputed lazily in renderer() (it reads the live time scale each redraw).
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return [this.paneView];
  }

  /** Build the per-band pixel rectangles from the stored points using the LIVE time scale, as a step
   *  function clipped at the as-of date. Returns [] when not yet attached or no points. */
  computeRects(): BandRect[] {
    if (!this.params || this.points.length === 0) return [];
    const timeScale = this.params.chart.timeScale();
    const rightEdge = timeScale.width();
    // The right clip = the x of the as-of date (so no band paints past it). If the as-of date isn't on
    // the visible scale, fall back to the pane's right edge (the as-of is the rightmost point anyway).
    let clipRight = rightEdge;
    if (this.asOfDate) {
      const asOfX = timeScale.timeToCoordinate(this.asOfDate as Time);
      if (asOfX !== null) clipRight = asOfX;
    }

    const rects: BandRect[] = [];
    for (let i = 0; i < this.points.length; i += 1) {
      const point = this.points[i];
      const startX = timeScale.timeToCoordinate(point.date as Time);
      if (startX === null) continue;
      // The band runs to the next point's date, or to the as-of clip for the last point.
      let endX: number;
      if (i + 1 < this.points.length) {
        const nextX = timeScale.timeToCoordinate(this.points[i + 1].date as Time);
        endX = nextX === null ? clipRight : nextX;
      } else {
        endX = clipRight;
      }
      const left = Math.max(0, Math.min(startX, clipRight));
      const right = Math.min(endX, clipRight);
      if (right <= left) continue;
      rects.push({ left, right, fill: regimeBandFill(point.label) });
    }
    return rects;
  }
}
