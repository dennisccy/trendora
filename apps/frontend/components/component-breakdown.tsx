import type { ScoreComponent } from "@/lib/api";
import { fmtHighProximity, HIGH_PROXIMITY_KEY } from "@/lib/high-proximity";
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
  // iter-3 — per-stock score components (leadership / entry quality / risk)
  rs_sector: "RS vs sector",
  rs_theme: "RS vs theme",
  high_proximity: "Proximity to 52w high",
  up_down_vol: "Volume trend",
  dist_rising_20: "Proximity to 20-DMA",
  contraction: "Volatility contraction",
  support_nearby: "Proximity to 50-DMA",
  structure: "Trend structure",
  reward_risk: "Reward / risk room",
  extension: "Extension above 50-DMA",
  atr_pct: "ATR %",
  liquidity: "Liquidity (low = risk)",
  regime: "Market regime",
  sector_strength: "Sector strength",
  gap_climax: "Earnings gap / climax",
  below_ma: "Below moving averages",
  rs_deterioration: "RS deterioration",
  // iter-3 — theme score components
  breadth: "Member breadth > 50-DMA",
  ma_participation: "MA-stack participation",
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
  // J-106: "Proximity to 52w high" shows its stored raw distance (a percent <= 0; 0 at a fresh high) —
  // the SAME value the /stocks leaderboard column re-displays (single source), not the opaque percentile.
  if (component.name === HIGH_PROXIMITY_KEY) return fmtHighProximity(component.raw ?? null);
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
