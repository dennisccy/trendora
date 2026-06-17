import { cn } from "@/lib/utils";

/**
 * Shared forward-return display helpers — the SINGLE formatting source for realized-return figures,
 * used by both System Health (J-09/J-10) and the Backtest scorecard (J-14). These RE-FORMAT a return
 * fraction the backend already computed; they never compute a return/excess client-side. NA (null)
 * renders as an em dash with n=0, and figures below `min_sample` are flagged with the `--warn` token —
 * an honest, never-fabricated presentation (palette tokens only, per the DESIGN SYSTEM).
 */

/** Format a return fraction (0.0123 -> "+1.23%"); null/NA renders an em dash. */
export function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

/** Positive returns green, negative red, zero/NA muted — palette tokens only (DESIGN SYSTEM). */
export function returnClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "text-text-muted";
  if (value > 0) return "text-pos";
  if (value < 0) return "text-neg";
  return "text-text";
}

/** Sample size beside every figure; flagged with the warn token when n < min_sample (low sample). */
export function SampleSize({ n, min }: { n: number; min: number }) {
  const low = n < min;
  return (
    <span
      className={cn("num text-xs", low ? "text-warn" : "text-text-faint")}
      title={low ? `Low sample — n below the ${min} minimum; treat as indicative only` : undefined}
    >
      n={n}
      {low ? " ⚠" : ""}
    </span>
  );
}

/** A return figure + its sample size — the shared cell rendered across the evidence tables. */
export function Return({ value, n, min }: { value: number | null; n: number; min: number }) {
  return (
    <span className="inline-flex items-center justify-end gap-2">
      <span className={cn("num font-semibold", returnClass(value))}>{fmtPct(value)}</span>
      <SampleSize n={n} min={min} />
    </span>
  );
}

/**
 * Max-drawdown display helpers (iter-27, J-86). A max drawdown is a true peak-to-trough decline read
 * VERBATIM from the stored `forward_returns.max_drawdown` — it is <= 0 always (or NA), so it grades on
 * the negative/red scale: a worse (more negative) drawdown reads redder; exactly 0 / NA is muted. These
 * RE-FORMAT a stored figure; they never compute a drawdown client-side.
 */

/** Format a drawdown fraction (-0.083 -> "-8.30%"); null/NA renders an em dash. Always <= 0 when present. */
export function fmtMdd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const pct = value * 100;
  // a drawdown is <= 0; print its sign honestly (0 -> "0.00%", never "+").
  return `${pct.toFixed(2)}%`;
}

/** Drawdown colour: a real (negative) drawdown is red; exactly 0 or NA is muted (never green — it is risk). */
export function mddClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "text-text-muted";
  if (value < 0) return "text-neg";
  return "text-text-muted";
}

/** A max-drawdown figure cell — paired beside a forward-return cell (J-86). NA renders an em dash. */
export function MaxDrawdown({ value }: { value: number | null | undefined }) {
  return <span className={cn("num font-semibold", mddClass(value))}>{fmtMdd(value)}</span>;
}
