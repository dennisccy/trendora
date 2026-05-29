import type { ScoreComponent } from "@/lib/api";
import { cn } from "@/lib/utils";

// Human labels for the canonical component keys (presentation only — the values are computed
// once in the backend engine and only re-formatted here).
const LABELS: Record<string, string> = {
  rs_spy_1m: "RS vs SPY · 1m",
  rs_spy_3m: "RS vs SPY · 3m",
  rs_spy_6m: "RS vs SPY · 6m",
  ma_stack: "MA stack",
  dist_from_high: "Dist. from 52w high",
  vol_trend: "Volume trend",
  index_ma_stack: "Index MA stack",
  breadth_above_50dma: "Breadth > 50-DMA",
  breadth_above_200dma: "Breadth > 200-DMA",
  new_high_low: "Net new highs",
  vix_gate: "VIX gate",
};

function prettyName(name: string): string {
  return LABELS[name] ?? name;
}

function detail(component: ScoreComponent): string {
  if (!component.available) return "NA";
  if (component.name === "vix_gate") {
    const op = component.elevated ? "≥" : "<";
    return `VIX ${component.value ?? "—"} ${op} ${component.threshold ?? "—"} (×${component.factor ?? "—"})`;
  }
  if (typeof component.percentile === "number") {
    return `pctl ${(component.percentile * 100).toFixed(0)}`; // sector rows rank cross-sectionally
  }
  if (typeof component.value === "number") {
    return component.value.toFixed(2); // regime sub-scores
  }
  return "—";
}

/** Renders a score's named component breakdown — explainability, never a bare number. */
export function ComponentBreakdown({
  components,
  className,
}: {
  components: ScoreComponent[];
  className?: string;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 text-xs uppercase tracking-wide text-text-faint">
        <span>Component</span>
        <span className="text-right">Detail</span>
        <span className="text-right">Contribution</span>
      </div>
      {components.map((component) => (
        <div
          key={component.name}
          className="grid grid-cols-[1fr_auto_auto] items-center gap-x-4 text-xs"
        >
          <span className="text-text-muted">{prettyName(component.name)}</span>
          <span className={cn("num text-right", component.available ? "text-text-faint" : "text-warn")}>
            {detail(component)}
          </span>
          <span className="num text-right text-text">
            {component.contribution == null ? "—" : component.contribution.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}
