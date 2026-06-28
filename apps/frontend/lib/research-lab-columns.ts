/**
 * J-114 — the per-horizon column ORDER for the four all-horizon Research lab tables.
 *
 * Pure view-transform helper: given the config-driven horizon set (`config.walk_forward.horizons`,
 * reported by every lab payload as `data.horizons` — never a hardcoded [1,5,10,20,60]), it returns the
 * ordered column descriptors the Factor / Regime / Phase-Severity / Regime×Phase×Factor tables map over.
 *
 * The order is GROUPED — ALL forward-return columns first (in the given horizon order), THEN all
 * max-drawdown columns (in the same horizon order) — never interleaved (no Fwd → MDD → Fwd alternation).
 * This matches the /stocks · /themes · /sectors leaderboard grouping (J-86).
 *
 * It describes only WHICH column to render and in what order — it reads, recomputes, and refetches NO
 * figure. Every displayed value stays byte-identical to its canonical source; only the column position
 * changes (Single source of truth / No recompute in the read path).
 */

/** A per-horizon column metric: the top/cohort forward return (`fwd`) or its paired max-drawdown (`mdd`). */
export type HorizonMetric = "fwd" | "mdd";

/** One per-horizon column descriptor: its metric and its horizon (trading days). */
export interface HorizonColumn {
  metric: HorizonMetric;
  horizon: number;
}

/** A stable React/key string for a horizon column (`fwd-5` / `mdd-20`). */
export function horizonColumnKey(col: HorizonColumn): string {
  return `${col.metric}-${col.horizon}`;
}

/**
 * The grouped per-horizon column order (J-114): every forward-return column first (ascending horizon
 * order as supplied), then every max-drawdown column in the same horizon order. Never interleaved.
 */
export function groupedHorizonColumns(horizons: number[]): HorizonColumn[] {
  return [
    ...horizons.map((horizon) => ({ metric: "fwd" as const, horizon })),
    ...horizons.map((horizon) => ({ metric: "mdd" as const, horizon })),
  ];
}
