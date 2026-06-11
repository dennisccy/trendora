/**
 * The ONE shared market-regime label → risk-family → color mapping (J-44 + J-45 / Capability 37).
 *
 * BOTH regime-band surfaces — the dashboard "Major indexes & regime" card (J-44) and the regime bands
 * behind the stock-detail price chart (J-45) — import THIS module, so the SAME stored regime label maps
 * to the SAME color on every surface (coherence: same date ⇒ same color everywhere). There is no second,
 * duplicated mapping anywhere.
 *
 * The six configured regime labels collapse into THREE risk families:
 *   - risk-on  : "Strong risk-on", "Risk-on"            → green  (--pos)
 *   - neutral  : "Narrow leadership", "Choppy"          → amber  (--warn)
 *   - risk-off : "Defensive", "Risk-off"                → red    (--neg)
 *
 * Colors are taken ONLY from the DESIGN SYSTEM palette tokens (`--pos`/`--warn`/`--neg`); the soft band
 * fill uses a low-alpha rgba of the same hue (no new effect, no arbitrary color). A label outside the six
 * (should never happen — the backend serves only stored labels) falls back to the neutral family so a
 * band still renders rather than crashing.
 *
 * This module performs NO regime computation — it only classifies a STORED label the backend served.
 */

export type RiskFamily = "risk-on" | "neutral" | "risk-off";

/** The DESIGN SYSTEM palette hex for each family (the same tokens the regime badges use). */
const FAMILY_HEX: Record<RiskFamily, string> = {
  "risk-on": "#34d399", // --pos
  neutral: "#fbbf24", // --warn
  "risk-off": "#f87171", // --neg
};

/** Map a stored regime label to its risk family. Unknown labels fall back to neutral (band still draws). */
export function regimeFamily(label: string): RiskFamily {
  if (label === "Strong risk-on" || label === "Risk-on") return "risk-on";
  if (label === "Defensive" || label === "Risk-off") return "risk-off";
  // "Narrow leadership" · "Choppy" · any unexpected label
  return "neutral";
}

/** The solid family hue (used for the legend swatch / hover label text). */
export function regimeColor(label: string): string {
  return FAMILY_HEX[regimeFamily(label)];
}

/**
 * The soft background-band fill for a regime label as an rgba() string at the given alpha (default a
 * subtle 0.12 so price/index lines stay readable on top). Same hue as `regimeColor`, just low-alpha —
 * no new effect, no arbitrary color.
 */
export function regimeBandFill(label: string, alpha = 0.12): string {
  const hex = regimeColor(label);
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** Human-readable family label for the legend (e.g. "Risk-on"). */
export function familyLabel(family: RiskFamily): string {
  switch (family) {
    case "risk-on":
      return "Risk-on";
    case "risk-off":
      return "Risk-off";
    default:
      return "Neutral";
  }
}

/** The three families in display order, for a band legend. */
export const RISK_FAMILIES: RiskFamily[] = ["risk-on", "neutral", "risk-off"];

/** The family hue by family key (for a legend swatch). */
export function familyColor(family: RiskFamily): string {
  return FAMILY_HEX[family];
}
