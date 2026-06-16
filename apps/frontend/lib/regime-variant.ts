import type { badgeVariants } from "@/components/ui/badge";
import type { VariantProps } from "class-variance-authority";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/**
 * The single mapping from a STORED market-regime label to a Badge palette variant — shared by the
 * Dashboard (J-06) and the Stocks header (J-80) so the SAME stored label renders the SAME colour on
 * every surface. This is presentation only (a colour for a label); it computes / recomputes NO regime
 * value — the label + 0–100 score are served verbatim by `/api/dashboard`. One label → one colour, one
 * source of truth. The six labels come from `config.regime.labels` (served), grouped by risk posture:
 *   risk-on → `ok` (green) · defensive/risk-off → `danger` (red) · narrow/choppy → `warn` (amber).
 */
export function regimeVariant(label: string): BadgeVariant {
  if (label === "Strong risk-on" || label === "Risk-on") return "ok";
  if (label === "Defensive" || label === "Risk-off") return "danger";
  return "warn"; // Narrow leadership · Choppy
}
