/**
 * Lightweight-Charts series primitive that paints soft market-PHASE BACKGROUND BANDS behind a chart
 * (the J-97 Dashboard cross-view bottom pane). It is the phase-dimension analogue of
 * `regime-band-primitive.ts`: same `ISeriesPrimitive` / background-rect step-function pattern, fed by the
 * served full-history causal phase timeline and the same `lib/phase` colour mapping the Market-Phase card
 * timeline uses, so the same date shows the same phase colour everywhere (coherence).
 *
 * The bands are an HONEST STEP FUNCTION between snapshot dates: each timeline point owns the horizontal
 * span from its own date up to (not including) the next point's date; the last point extends to the right
 * edge — but, while a historical as-of is selected, NEVER past the resolved as-of x-coordinate (the post-D
 * region stays band-free / display-only behind the as-of marker, mirroring the regime primitive's J-49
 * treatment). A point with an empty/NA phase produces NO band (never a fabricated band).
 *
 * It computes NO phase — it only reads the served phase label per date and maps it to a palette colour via
 * `phaseBandFill`. Drawn on the BACKGROUND layer (`zOrder: 'bottom'`) so the index lines / severity /
 * P(bear) lines and the grid sit on top.
 */
import type {
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesPrimitive,
  PrimitivePaneViewZOrder,
  SeriesAttachedParameter,
  Time,
} from "lightweight-charts";

import { phaseBandFill } from "@/lib/phase";
import type { MarketPhaseTimelinePoint } from "@/lib/api";

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

class PhaseBandRenderer implements IPrimitivePaneRenderer {
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

class PhaseBandPaneView implements IPrimitivePaneView {
  constructor(private readonly source: PhaseBandPrimitive) {}

  zOrder(): PrimitivePaneViewZOrder {
    return "bottom"; // behind the index/severity/P(bear) lines and grid
  }

  renderer(): IPrimitivePaneRenderer {
    return new PhaseBandRenderer(this.source.computeRects());
  }
}

export class PhaseBandPrimitive implements ISeriesPrimitive<Time> {
  private params: SeriesAttachedParameter<Time> | null = null;
  private readonly paneView: PhaseBandPaneView;
  private points: MarketPhaseTimelinePoint[] = [];
  private asOfDate: string | null = null;

  constructor() {
    this.paneView = new PhaseBandPaneView(this);
  }

  /** Update the served phase timeline points + the as-of right bound, then request a redraw. When
   *  `asOfDate` is null the last band extends to the right edge (no clip); when set, the last band is
   *  clipped at the as-of x (post-D region stays band-free, J-49 treatment). */
  setData(points: MarketPhaseTimelinePoint[], asOfDate: string | null): void {
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

  /** Build the per-band pixel rectangles from the served phase timeline using the LIVE time scale, as a
   *  step function optionally clipped at the as-of date. A point with an empty/NA phase produces no band
   *  (never a fabricated band). Returns [] when not yet attached or no points. */
  computeRects(): BandRect[] {
    if (!this.params || this.points.length === 0) return [];
    const timeScale = this.params.chart.timeScale();
    const rightEdge = timeScale.width();
    // The right clip = the x of the as-of date (so no band paints past it) while historical; if the as-of
    // isn't provided / not on the visible scale, fall back to the pane's right edge (full history).
    let clipRight = rightEdge;
    if (this.asOfDate) {
      const asOfX = timeScale.timeToCoordinate(this.asOfDate as Time);
      if (asOfX !== null) clipRight = asOfX;
    }

    const rects: BandRect[] = [];
    for (let i = 0; i < this.points.length; i += 1) {
      const point = this.points[i];
      // NA / empty phase → no band (never fabricate a span for a missing label).
      if (!point.phase) continue;
      const startX = timeScale.timeToCoordinate(point.date as Time);
      if (startX === null) continue;
      // The band runs to the next point's date, or to the clip for the last point.
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
      rects.push({ left, right, fill: phaseBandFill(point.phase) });
    }
    return rects;
  }
}
