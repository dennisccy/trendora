/**
 * Lightweight-Charts series primitive that draws ONE clearly-visible vertical "as-of" divider line at
 * the resolved as-of date D, spanning the full chart height, with a small "as-of D" label (J-49 dashboard
 * "Major indexes & regime" card while browsing a historical date).
 *
 * It is the same as-of-divider visual treatment / label family the stock-detail price chart uses for its
 * J-20 forward-region boundary (the `--warn` palette token + an "as-of <date>" label) — so the product
 * reads as ONE design — but rendered as a true vertical divider so the dashboard's full-history context
 * (bars + bands extending PAST D, J-49) stays readable with an unmistakable "you are here" marker.
 *
 * It is DISPLAY-ONLY chrome: it positions a line at the date the server already resolved (`asOfDate`),
 * computes nothing, and is drawn only while a historical date is selected (no marker at the latest date).
 * Drawn on the foreground so it sits above the lines/bands but below the tooltip overlay.
 */
import type {
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesPrimitive,
  SeriesAttachedParameter,
  Time,
} from "lightweight-charts";

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

class AsOfMarkerRenderer implements IPrimitivePaneRenderer {
  constructor(
    private readonly x: number | null,
    private readonly color: string,
    private readonly label: string,
  ) {}

  draw(target: unknown): void {
    if (this.x === null) return;
    const bitmapTarget = target as BitmapTarget;
    bitmapTarget.useBitmapCoordinateSpace(
      ({ context: ctx, bitmapSize, horizontalPixelRatio, verticalPixelRatio }) => {
        const xPx = Math.round(this.x! * horizontalPixelRatio);
        if (xPx < 0 || xPx > bitmapSize.width) return;
        // The vertical divider line (dashed, the J-20 `--warn` family) spanning the full pane height.
        ctx.save();
        ctx.strokeStyle = this.color;
        ctx.lineWidth = Math.max(1, Math.round(1.5 * horizontalPixelRatio));
        ctx.setLineDash([
          Math.round(4 * verticalPixelRatio),
          Math.round(3 * verticalPixelRatio),
        ]);
        ctx.beginPath();
        ctx.moveTo(xPx, 0);
        ctx.lineTo(xPx, bitmapSize.height);
        ctx.stroke();

        // A compact "as-of <date>" pill at the top so the marker is self-labelling (same label family
        // as the price-chart's J-20 as-of marker). Drawn just right of the line, clamped into the pane.
        ctx.setLineDash([]);
        const fontPx = Math.round(11 * verticalPixelRatio);
        ctx.font = `${fontPx}px ui-monospace, monospace`;
        ctx.textBaseline = "top";
        const padX = Math.round(4 * horizontalPixelRatio);
        const padY = Math.round(3 * verticalPixelRatio);
        const textW = ctx.measureText(this.label).width;
        const boxW = textW + padX * 2;
        const boxH = fontPx + padY * 2;
        // Prefer the right side of the line; flip left if it would overflow the pane edge.
        let boxX = xPx + Math.round(3 * horizontalPixelRatio);
        if (boxX + boxW > bitmapSize.width) boxX = xPx - boxW - Math.round(3 * horizontalPixelRatio);
        const boxY = Math.round(4 * verticalPixelRatio);
        ctx.fillStyle = this.color;
        ctx.globalAlpha = 0.92;
        ctx.fillRect(boxX, boxY, boxW, boxH);
        ctx.globalAlpha = 1;
        ctx.fillStyle = "#0a0a0f"; // dark text on the warm pill (high-contrast, matches the dark theme)
        ctx.fillText(this.label, boxX + padX, boxY + padY);
        ctx.restore();
      },
    );
  }
}

class AsOfMarkerPaneView implements IPrimitivePaneView {
  constructor(private readonly source: AsOfMarkerPrimitive) {}

  renderer(): IPrimitivePaneRenderer {
    return new AsOfMarkerRenderer(
      this.source.computeX(),
      this.source.color,
      this.source.label,
    );
  }
}

export class AsOfMarkerPrimitive implements ISeriesPrimitive<Time> {
  private params: SeriesAttachedParameter<Time> | null = null;
  private readonly paneView: AsOfMarkerPaneView;
  private asOfDate: string | null = null;
  color = "#f59e0b"; // overwritten with the live `--warn` token by setData
  label = "";

  constructor() {
    this.paneView = new AsOfMarkerPaneView(this);
  }

  /** Set the as-of date (null ⇒ no marker, e.g. at the latest date), the resolved `--warn` color, and
   *  the pre-formatted label, then request a redraw. */
  setData(asOfDate: string | null, color: string, label: string): void {
    this.asOfDate = asOfDate;
    this.color = color;
    this.label = label;
    this.params?.requestUpdate();
  }

  attached(param: SeriesAttachedParameter<Time>): void {
    this.params = param;
  }

  detached(): void {
    this.params = null;
  }

  updateAllViews(): void {
    // x is recomputed lazily in the renderer (it reads the live time scale each redraw).
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return [this.paneView];
  }

  /** The pixel x of the as-of date on the LIVE time scale, or null when there is no marker / the date is
   *  off the visible scale. */
  computeX(): number | null {
    if (!this.params || !this.asOfDate) return null;
    const x = this.params.chart.timeScale().timeToCoordinate(this.asOfDate as Time);
    return x === null ? null : x;
  }
}
