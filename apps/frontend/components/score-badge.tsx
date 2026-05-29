import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type BadgeVariant = "ok" | "warn" | "danger" | "accent" | "default";

/**
 * A-E colour grade (green→red) using ONLY palette tokens, via the Badge variants:
 *   A/B → ok (green, strongest) · C → warn (amber, neutral) · D/E → danger (red, weakest).
 * The letter foregrounds the fine-grained bucket; the colour carries the coarse signal. The
 * raw 0-100 score is shown secondary (DESIGN SYSTEM: buckets first, raw secondary).
 */
export function bucketVariant(bucket: string): BadgeVariant {
  switch (bucket) {
    case "A":
    case "B":
      return "ok";
    case "C":
      return "warn";
    default:
      return "danger"; // D, E
  }
}

export function ScoreBadge({
  bucket,
  score,
  className,
}: {
  bucket: string;
  score: number;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <Badge variant={bucketVariant(bucket)} className="num font-semibold">
        {bucket}
      </Badge>
      <span className="num text-xs text-text-muted">{score.toFixed(2)}</span>
    </span>
  );
}
