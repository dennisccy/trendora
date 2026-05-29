import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type BadgeVariant = "ok" | "warn" | "danger" | "accent" | "default";

/**
 * A-E colour grade (green→red) using ONLY palette tokens, via the Badge variants:
 *   A/B → ok (green, strongest) · C → warn (amber, neutral) · D/E → danger (red, weakest).
 * The letter foregrounds the fine-grained bucket; the colour carries the coarse signal. The
 * raw 0-100 score is shown secondary (DESIGN SYSTEM: buckets first, raw secondary).
 *
 * `invert` flips the colour for the Risk score, which is a *danger* score (higher = MORE
 * dangerous): a high Risk bucket (A/B) is red, a low one (D/E) is green — graded by danger
 * direction. The bucket LETTER is unchanged (it still reflects the raw 0-100 position).
 */
export function bucketVariant(bucket: string, invert = false): BadgeVariant {
  if (bucket === "C") return "warn";
  const strong = bucket === "A" || bucket === "B";
  if (invert) return strong ? "danger" : "ok"; // Risk: high danger = red, low danger = green
  return strong ? "ok" : "danger";
}

export function ScoreBadge({
  bucket,
  score,
  invert = false,
  className,
}: {
  bucket: string;
  score: number;
  invert?: boolean;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <Badge variant={bucketVariant(bucket, invert)} className="num font-semibold">
        {bucket}
      </Badge>
      <span className="num text-xs text-text-muted">{score.toFixed(2)}</span>
    </span>
  );
}
