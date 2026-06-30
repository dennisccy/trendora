"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ShieldCheck } from "lucide-react";

import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { claimSurface, regimeLabel } from "@/lib/evidence";
import { fetchEvidence, type CertifiedClaim, type EvidenceLedgerResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: EvidenceLedgerResponse }
  | { kind: "error" };

/** The five fields every certified-claims row carries — the claim-row layout, named once so the empty
 *  state can enumerate them (honest schema, no fabricated claim) and the real `ClaimRow` renders them. */
const CLAIM_FIELDS = [
  "Hypothesis",
  "Out-of-sample verdict",
  "Control comparison (vs SPY)",
  "Registration date",
  "Forward-walk score-to-date",
] as const;

function verdictVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  if (status === "PASS") return "accent";
  if (status === "INSUFFICIENT") return "warn";
  if (status === "FAIL") return "danger";
  return "default";
}

export default function EvidencePage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchEvidence(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  const claims = state.kind === "ok" ? state.data.claims : [];

  return (
    <div className="space-y-4">
      <PageHeading
        title="Evidence"
        subtitle="The certified-claims ledger — the single source of proven-ness. A signal reads “Proven” ONLY when a referee-certified, out-of-sample, control-beating claim backs it; everything else honestly reads “Not yet proven.”"
      />

      {state.kind === "loading" ? <EvidenceSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The certified-claims ledger could not load from the API. Nothing is fabricated — every signal
              continues to read “Not yet proven.” Confirm the backend is running and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && claims.length === 0 ? <EvidenceEmptyState /> : null}

      {state.kind === "ok" && claims.length > 0 ? (
        <div className="space-y-3" data-testid="evidence-claim-list">
          {claims.map((claim, index) => (
            <ClaimRow key={`${claim.signal ?? "claim"}-${index}`} claim={claim} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** The honest empty state (today's reality — zero certified claims). It enumerates the claim-row layout
 *  fields so the page's structure is visible WITHOUT fabricating a claim, and states plainly that every
 *  signal currently reads “Not yet proven.” */
function EvidenceEmptyState() {
  return (
    <Card data-testid="evidence-empty">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">No certified claims yet</h2>
        </div>
        <p className="max-w-2xl text-sm text-text-muted">
          No certified claims yet — every signal currently reads{" "}
          <span className="font-medium text-text">Not yet proven</span>. A claim earns a place here only
          after the statistical referee certifies it on a sealed out-of-sample holdout that beats its
          controls (SPY / QQQ / sector ETF / random same-sector) with multiple-testing correction. Until
          then nothing is shown as a confident, proven number.
        </p>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-text-faint">
            Each certified claim will show
          </p>
          <ul className="grid gap-1.5 sm:grid-cols-2" data-testid="evidence-claim-fields">
            {CLAIM_FIELDS.map((field) => (
              <li key={field} className="flex items-center gap-2 text-sm text-text-muted">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-border-strong" aria-hidden />
                {field}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-text-faint">
          Each row will link back to the surface it backs (e.g. the{" "}
          <Link href="/stocks" className="text-accent hover:underline">
            Stocks leaderboard
          </Link>
          ), and each “Proven” badge there will link to its backing row here.
        </p>
      </CardContent>
    </Card>
  );
}

/** One certified-claims ledger row — the claim-row layout exercised once ≥1 claim is certified. Renders
 *  the five fields VERBATIM from the served entry; carries the `id={signal-…}` anchor a “Proven” badge
 *  links to, and a link back to the surface it backs (claim → surface linkback). */
function ClaimRow({ claim }: { claim: CertifiedClaim }) {
  const surface = claimSurface(claim);
  const regime = regimeLabel(claim);
  const anchorId = claim.signal ? `signal-${claim.signal}` : undefined;
  const verdict = claim.verdict ?? { status: "", reason: "" };
  return (
    <Card id={anchorId} data-testid="evidence-claim-row" className="scroll-mt-20">
      <CardContent className="space-y-3 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={verdictVariant(verdict.status)}>{verdict.status || "—"}</Badge>
            {surface.titleIsSignalKey ? (
              <span className="num text-sm font-semibold text-text">{surface.title}</span>
            ) : (
              <span className="text-sm font-semibold text-text">{surface.title}</span>
            )}
            {/* J-04: a regime-conditioned claim is clearly labeled with the regime it holds in (read
                verbatim from the cohort's own selector). Hidden entirely for a score row (no regime) — so
                the leadership row looks unchanged. */}
            {regime ? (
              <Badge variant="accent" data-testid="evidence-claim-regime">
                Regime: {regime}
              </Badge>
            ) : null}
          </div>
          <Link
            href={surface.href}
            className="text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
            data-testid="evidence-claim-linkback"
          >
            Backs: {surface.label} →
          </Link>
        </div>

        {/* Honest anti-hype framing for a non-score (setup) claim — historical out-of-sample evidence,
            never a buy/sell or return promise. Absent for a score row (subtitle === null). */}
        {surface.subtitle ? (
          <p className="text-xs text-text-muted" data-testid="evidence-claim-subtitle">
            {surface.subtitle}
          </p>
        ) : null}

        <dl className="grid gap-3 sm:grid-cols-2">
          <Field label="Hypothesis">
            <ClaimHypothesis claim={claim.claim} />
          </Field>
          <Field label="Out-of-sample verdict">
            <span className="text-text">
              {verdict.status || "—"}
              {verdict.holdout_edge != null ? ` · holdout edge ${fmtSigned(verdict.holdout_edge)}` : ""}
            </span>
            {verdict.reason ? <p className="text-xs text-text-faint">{verdict.reason}</p> : null}
          </Field>
          <Field label="Control comparison (vs SPY)">
            <span className="text-text">
              {verdict.control_excess != null ? fmtSigned(verdict.control_excess) : "—"}
            </span>
          </Field>
          <Field label="Registration date">
            <span className="num text-text">{claim.register_date ?? "—"}</span>
          </Field>
          <Field label="Forward-walk score-to-date">
            {claim.forward_walk == null ? (
              <span className="text-text-faint">Pending — monitored as new data matures</span>
            ) : (
              <span className="num text-text">{String(claim.forward_walk)}</span>
            )}
          </Field>
        </dl>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs uppercase tracking-wide text-text-faint">{label}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

/** Render the claim's cohort selectors (the hypothesis) verbatim as compact key=value chips — read-only. */
function ClaimHypothesis({ claim }: { claim: Record<string, unknown> }) {
  const entries = Object.entries(claim).filter(([key]) => key !== "signal");
  if (entries.length === 0) {
    return <span className="text-text-muted">—</span>;
  }
  return (
    <div className="flex flex-wrap gap-1">
      {entries.map(([key, value]) => (
        <Badge key={key} variant="default" className="num whitespace-nowrap text-[11px]">
          {key}={String(value)}
        </Badge>
      ))}
    </div>
  );
}

/** Format a signed fraction as a percent with an explicit sign (e.g. +1.80% / -0.40%). Display-only. */
function fmtSigned(value: number): string {
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

function EvidenceSkeleton() {
  return (
    <Card className="space-y-3 p-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className={cn("h-5 animate-pulse rounded bg-surface-2", i === 0 ? "w-40" : "w-full")} />
      ))}
    </Card>
  );
}
