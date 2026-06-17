/**
 * J-86 — the magnitude-graded max-drawdown colour scale (single source of truth).
 *
 * A max drawdown is a true peak-to-trough decline read VERBATIM from the stored
 * `forward_returns.max_drawdown`: it is <= 0 when present (or NA). This module maps the MAGNITUDE of a
 * real drawdown to a severity colour so a deeper drawdown reads visibly more severe — a pure
 * presentation transform over the already-served figure (it never computes a drawdown).
 *
 * Token discipline (anti-goal 10 — "no magic numbers / no hardcoded hex"): every band's colour is a
 * `color-mix` over the EXISTING design tokens `--neg` (risk red) and `--text-muted` — a shallow drawdown
 * mixes more muted-grey into red (least severe); a deep drawdown is near-pure `--neg` (most severe). No
 * new hex anywhere. (Tailwind v3's `text-neg/40` opacity modifier is a no-op here because `--neg` is a
 * plain hex var with no `<alpha-value>` channel, so we grade via `color-mix` arbitrary-value utilities,
 * which compile to real graded colour from the same tokens.)
 *
 * NA / undefined / exactly-0 are NOT real drawdowns and stay muted (`--text-muted`) — honest
 * partial-window discipline: NA must never be coloured as a real drawdown.
 */

/** The muted token for NA / undefined / exactly-flat drawdowns (never a graded red). */
export const MUTED_CLASS = "text-text-muted";

/**
 * Severity bands, shallowest → deepest. `maxMagnitude` is the inclusive upper bound (as a positive
 * fraction) of |drawdown| for the band; the last band's `Infinity` catches the most severe. Each
 * `className` is a Tailwind arbitrary-value `color-mix` over the existing `--neg` / `--text-muted`
 * tokens — the % of `--neg` rises with severity (40% → 60% → 80% → 100% pure red).
 *
 * Thresholds are presentation tokens (named, not inline magic numbers): a |drawdown| up to 2% reads
 * as a shallow/least-severe decline; deeper than 15% reads as the most severe.
 */
export const MDD_BANDS: ReadonlyArray<{ maxMagnitude: number; className: string }> = [
  // |dd| <= 2% — shallow: 40% red mixed into the muted token (least severe).
  { maxMagnitude: 0.02, className: "text-[color-mix(in_srgb,var(--neg)_40%,var(--text-muted))]" },
  // |dd| <= 5% — moderate: 60% red.
  { maxMagnitude: 0.05, className: "text-[color-mix(in_srgb,var(--neg)_60%,var(--text-muted))]" },
  // |dd| <= 15% — deep: 80% red.
  { maxMagnitude: 0.15, className: "text-[color-mix(in_srgb,var(--neg)_80%,var(--text-muted))]" },
  // |dd| > 15% — most severe: full `--neg` (pure risk red).
  { maxMagnitude: Infinity, className: "text-[var(--neg)]" },
] as const;

/**
 * Resolve a max-drawdown fraction to its severity colour class.
 *  - null / undefined (NA) -> muted.
 *  - exactly 0 (flat — no real drawdown) -> muted.
 *  - a negative drawdown -> the first band whose `maxMagnitude` bound covers its magnitude.
 * A more-negative value never maps to an earlier (less-severe) band (monotonic in magnitude).
 */
export function mddColorClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return MUTED_CLASS;
  if (value >= 0) return MUTED_CLASS; // exactly 0 (or a non-drawdown positive, never expected) is muted
  const magnitude = Math.abs(value);
  for (const band of MDD_BANDS) {
    if (magnitude <= band.maxMagnitude) return band.className;
  }
  // Unreachable (the last band is Infinity), but stay safe.
  return MDD_BANDS[MDD_BANDS.length - 1].className;
}
