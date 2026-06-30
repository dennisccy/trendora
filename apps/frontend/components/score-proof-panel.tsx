"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  formatEvidencePct,
  formatPValue,
  proofFieldsFor,
  type ProvenSignal,
} from "@/lib/evidence";

/**
 * J-02 proof drill-down (goal-mcp-loop iter-2). On a stock's detail page, when a score is PROVEN this
 * renders a calm, collapsed-by-default "Why proven?" disclosure that expands IN PLACE to let the user
 * audit *why* the score is considered proven:
 *   - the out-of-sample test — verdict status + holdout edge + p-value (+ the sealed-holdout cohort size);
 *   - the control comparison vs SPY — the cohort's excess over the benchmark control the referee used;
 *   - the certified-claim id + registration date — linking to the backing `/evidence` ledger row.
 *
 * It FETCHES NOTHING and RECOMPUTES NOTHING — every value is read VERBATIM from the already-fetched
 * `proven_signals` map (the single source of proven-ness), via the pure `proofFieldsFor` extractor. When
 * the signal is NOT proven it renders NOTHING (fail-safe: no empty panel, no fabricated confidence). It is
 * rendered ONLY on the Stock-detail score card — never on the leaderboard (the proof must not leak beside
 * the inline badge there). Additive only: the score number it sits below is unchanged.
 */
export function ScoreProofPanel({
  signal,
  provenSignals,
  className,
}: {
  /** The signal key this score maps to (e.g. "leadership_score"). */
  signal: string;
  /** The served proven-signal map (null/undefined while loading or on a fetch failure → renders nothing). */
  provenSignals: Record<string, ProvenSignal> | null | undefined;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const fields = proofFieldsFor(signal, provenSignals);

  // FAIL-SAFE: a signal that is not proven shows no disclosure at all (never an empty panel).
  if (!fields) {
    return null;
  }

  return (
    <div
      className={cn("rounded-md border border-border bg-surface-2", className)}
      data-testid="score-proof"
    >
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        data-testid="score-proof-toggle"
        className={cn(
          "flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-xs font-medium text-text-muted",
          "transition-colors hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        <span className="inline-flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />
          Why proven?
        </span>
        <ChevronDown
          className={cn("h-3.5 w-3.5 shrink-0 transition-transform duration-200", open && "rotate-180")}
          aria-hidden
        />
      </button>

      {open ? (
        <dl className="space-y-3 border-t border-border px-3 py-3" data-testid="score-proof-body">
          {/* Out-of-sample test — the referee's verdict status + holdout edge + p-value, read verbatim. */}
          <ProofField label="Out-of-sample test">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <Badge variant="accent" className="text-[11px]">
                {fields.status || "—"}
              </Badge>
              {fields.holdoutEdge != null ? (
                <span className="text-text" data-testid="proof-holdout-edge">
                  holdout edge <span className="num">{formatEvidencePct(fields.holdoutEdge)}</span>
                </span>
              ) : null}
              {fields.pValue != null ? (
                <span className="text-text-muted" data-testid="proof-p-value">
                  p = <span className="num">{formatPValue(fields.pValue)}</span>
                </span>
              ) : null}
            </div>
            {fields.cohortN != null ? (
              <p className="mt-1 text-[11px] text-text-faint">
                Sealed holdout cohort:{" "}
                <span className="num">{fields.cohortN.toLocaleString()}</span> observations
              </p>
            ) : null}
          </ProofField>

          {/* Control comparison — the cohort's excess over the SPY benchmark control the referee used. */}
          <ProofField label="Control comparison">
            <span className="num text-text" data-testid="proof-control-excess">
              {fields.controlExcess != null ? formatEvidencePct(fields.controlExcess) : "—"}
            </span>{" "}
            <span className="text-[11px] text-text-faint">vs SPY (benchmark control)</span>
          </ProofField>

          {/* Certified-claim id + registration date, linking to the backing /evidence ledger row. */}
          <ProofField label="Certified claim">
            <span className="num text-text" data-testid="proof-claim-id">
              {fields.claimId}
            </span>
            <div className="mt-1">
              <Link
                href={fields.href}
                data-testid="proof-evidence-link"
                className="text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
              >
                View backing evidence row →
              </Link>
            </div>
          </ProofField>
        </dl>
      ) : null}
    </div>
  );
}

function ProofField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <dt className="text-[10px] uppercase tracking-wide text-text-faint">{label}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}
