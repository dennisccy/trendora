import Link from "next/link";
import { Shield, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { resolveEvidenceStatus, type ProvenSignal } from "@/lib/evidence";

/**
 * The inline evidence-status chip (goal-mcp-loop iter-1) — a calm, unmissable "Proven / Not yet proven"
 * marker that rides ALONGSIDE a score (never replacing it). It is purely additive: the score it sits beside
 * is unchanged.
 *
 * The evidence ledger is the SINGLE source of proven-ness — this badge NEVER computes it. It reads the
 * served `proven_signals` map via the pure `resolveEvidenceStatus` resolver:
 *   - PRESENT & proven  → "Proven" (calm accent token), a link to its `/evidence` backing entry;
 *   - ABSENT / null map  → "Not yet proven" (muted token), no link — the FAIL-SAFE default.
 * Against today's empty ledger every signal renders "Not yet proven" (no hype, no fabricated confidence).
 */
export function EvidenceStatusBadge({
  signal,
  provenSignals,
  className,
}: {
  /** The signal key this score maps to (e.g. "leadership_score"). */
  signal: string;
  /** The served proven-signal map (null/undefined while loading or on a fetch failure → fail-safe). */
  provenSignals: Record<string, ProvenSignal> | null | undefined;
  className?: string;
}) {
  const status = resolveEvidenceStatus(signal, provenSignals);

  if (status.proven && status.href) {
    const claim = status.claim;
    const title = claim
      ? `Proven — certified out-of-sample (registered ${claim.register_date ?? "—"}). Click to audit the backing evidence.`
      : "Proven — certified out-of-sample. Click to audit the backing evidence.";
    return (
      <Link
        href={status.href}
        title={title}
        data-testid="evidence-badge"
        data-proven="true"
        className="inline-flex rounded-md focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
      >
        <Badge
          variant="accent"
          className={cn(
            "cursor-pointer whitespace-nowrap text-[11px] transition-colors hover:bg-surface active:bg-bg",
            className,
          )}
        >
          <ShieldCheck className="h-3 w-3 shrink-0" aria-hidden />
          {status.label}
        </Badge>
      </Link>
    );
  }

  return (
    <Badge
      variant="default"
      title="Not yet proven — no certified out-of-sample evidence backs this signal yet (see the Evidence ledger)."
      data-testid="evidence-badge"
      data-proven="false"
      className={cn("whitespace-nowrap text-[11px] text-text-faint", className)}
    >
      <Shield className="h-3 w-3 shrink-0 opacity-70" aria-hidden />
      {status.label}
    </Badge>
  );
}
