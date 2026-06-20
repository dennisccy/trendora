/**
 * The ONE shared market-PHASE label → stress-posture → color mapping (J-87 + J-97).
 *
 * BOTH market-phase surfaces — the dashboard "Market Phase & Severity" card timeline (J-89, the compact
 * SVG step function) and the J-97 cross-view chart's phase bands (the `lightweight-charts` background
 * primitive) — import THIS module, so the SAME served phase label maps to the SAME color on every surface
 * (coherence: same date ⇒ same color everywhere). There is no second, duplicated mapping anywhere.
 *
 * The five configured phase labels (Expansion / Pullback / Correction / Bear / Recovery — served verbatim
 * in `MarketPhaseResponse.labels`, never hard-coded here as the source) collapse into THREE stress
 * postures, mirroring the regime risk-families (`lib/regime`):
 *   - calm      : "Expansion", "Recovery"   → green  (--pos)
 *   - caution   : "Pullback"                → amber  (--warn)
 *   - stress    : "Correction", "Bear"      → red    (--neg)
 *
 * Colors are taken ONLY from the DESIGN SYSTEM palette tokens (`--pos`/`--warn`/`--neg`); the soft band
 * fill uses a low-alpha rgba of the same hue (no new effect, no arbitrary color). A label outside the five
 * (should never happen — the backend serves only stored labels) falls back to the calm posture so a band
 * still renders rather than crashing.
 *
 * This module performs NO phase computation — it only classifies a STORED label the backend served.
 */

export type PhasePosture = "calm" | "caution" | "stress";

/** The DESIGN SYSTEM palette hex for each posture (the SAME tokens the regime mapping + the card badges
 *  use — `lib/regime` FAMILY_HEX, kept in lockstep so the two lenses read as one design). */
const POSTURE_HEX: Record<PhasePosture, string> = {
  calm: "#34d399", // --pos
  caution: "#fbbf24", // --warn
  stress: "#f87171", // --neg
};

/** The CSS custom-property each posture maps to (for the card SVG fills, which can use `var(--token)`). */
const POSTURE_VAR: Record<PhasePosture, string> = {
  calm: "--pos",
  caution: "--warn",
  stress: "--neg",
};

/** Map a served phase label to its stress posture. Unknown labels fall back to calm (a band still draws). */
export function phasePosture(label: string): PhasePosture {
  if (label === "Bear" || label === "Correction") return "stress";
  if (label === "Pullback") return "caution";
  // "Expansion" · "Recovery" · any unexpected label
  return "calm";
}

/** The phase label → a `var(--token)` CSS color string (used by the card's SVG step-function fills). */
export function phaseFillVar(label: string): string {
  return `var(${POSTURE_VAR[phasePosture(label)]})`;
}

/** The solid posture hue hex (used for a legend swatch / the canvas band-primitive resolved fill base). */
export function phaseColor(label: string): string {
  return POSTURE_HEX[phasePosture(label)];
}

/**
 * The soft background-band fill for a phase label as an rgba() string at the given alpha (default a subtle
 * 0.16 so the index lines stay readable on top). Same hue as `phaseColor`, just low-alpha — no new effect,
 * no arbitrary color. Used by the `lightweight-charts` phase-band primitive, which needs a resolved color
 * string (a canvas `fillStyle` cannot read a `var(--token)`).
 */
export function phaseBandFill(label: string, alpha = 0.16): string {
  const hex = phaseColor(label);
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** Human-readable posture label for a legend (e.g. "Calm"). */
export function postureLabel(posture: PhasePosture): string {
  switch (posture) {
    case "calm":
      return "Calm";
    case "caution":
      return "Caution";
    default:
      return "Stress";
  }
}

/** The three postures in display order, for a band legend. */
export const PHASE_POSTURES: PhasePosture[] = ["calm", "caution", "stress"];

/** The posture hue hex by posture key (for a legend swatch). */
export function postureColor(posture: PhasePosture): string {
  return POSTURE_HEX[posture];
}
