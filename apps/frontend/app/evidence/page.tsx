"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ShieldCheck } from "lucide-react";

import { PageHeading } from "@/components/page-heading";
import { fmtMdd } from "@/components/forward-return";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  claimAnchorId,
  claimSurface,
  formatDays,
  formatStreak,
  insufficientLabel,
  regimeLabel,
  resolveDrawdownExpectationsPanelState,
  type DistributionCell,
  type LossStreakCell,
} from "@/lib/evidence";
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

  // Honor the URL hash AFTER the rows mount so a "Proven" badge deep-link (e.g.
  // `/evidence#combination-…`, or the signal-/factor-cohort anchors) actually scrolls its backing row into
  // view. The claim rows render only once the async fetch resolves, so the browser's native one-shot hash
  // scroll fires too early (before the target row exists in the DOM) and never lands — this re-applies it on
  // the load→ok transition, once the matching row is present. No-op when there is no hash or no matching row
  // (never fabricates a scroll for a missing anchor); respects each row's `scroll-mt-20` offset via
  // `block:"start"`. Fixes the deep-link scroll gap for ALL evidence anchors, not just the combination row.
  useEffect(() => {
    if (state.kind !== "ok") return;
    const raw = typeof window !== "undefined" ? window.location.hash.slice(1) : "";
    if (!raw) return;
    const id = decodeURIComponent(raw);
    const frame = requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => cancelAnimationFrame(frame);
  }, [state.kind]);

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
  // The row's deep-link anchor — the SHARED `claimAnchorId` every "Proven" badge agrees on: a score row
  // keeps its `signal-${signal}` id (J-02/J-05 deep-links unchanged); a signal-less plain-factor decile
  // cohort (iter-8 — vcp_contraction) derives its stable cohort anchor so the Research factor-lab "Proven"
  // badge lands on THIS row; any other signal-less row (the event-study row) stays `undefined` (unchanged).
  const anchorId = claimAnchorId(claim) ?? undefined;
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

        <DrawdownExpectationsPanel claim={claim} />
      </CardContent>
    </Card>
  );
}

/** J-25 — the phase-conditional drawdown & dry-spell expectations panel: an additive section inside the
 *  SAME claim card, below the existing field grid. Renders NOTHING when `expectations` is absent/null with
 *  no status field (mirrors the Stock-detail RiskBudgetCard's "return null when absent" precedent,
 *  iter-40) — never an error boundary, never a blank placeholder. Reads `claim.expectations` VERBATIM — no
 *  client-side recompute; every figure is the served median/p90/streak, re-formatted only. Renders for ANY
 *  claim regardless of its PASS/FAIL verdict (outcome-neutral, J-25) — descriptive history, never a
 *  forecast.
 *
 *  ops-hardening iter-29 (AG-8): branches on `resolveDrawdownExpectationsPanelState` (the single, pure
 *  authority) so a genuine per-claim compute failure THIS request (`expectations_status === "unavailable"`)
 *  renders a calm inline note instead of being indistinguishable from the pre-existing "not applicable"
 *  (absent) case. */
function DrawdownExpectationsPanel({ claim }: { claim: CertifiedClaim }) {
  const state = resolveDrawdownExpectationsPanelState(claim);
  if (state.kind === "absent") {
    return null;
  }
  if (state.kind === "unavailable") {
    // A routine transient-failure disclosure, not an error banner — same calm `text-text-faint` treatment
    // the "Pending — monitored as new data matures" forward-walk cell above already uses on this card.
    return (
      <div className="border-t border-border pt-3" data-testid="evidence-expectations-unavailable">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
          Historical drawdown &amp; dry-spell expectations
        </h3>
        <p className="mt-0.5 text-xs text-text-faint">
          Unavailable — monitored and refreshed as new data arrives.
        </p>
      </div>
    );
  }
  const { expectations } = state;
  return (
    <div className="space-y-2 border-t border-border pt-3" data-testid="evidence-expectations-panel">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-text-faint">
          Historical drawdown &amp; dry-spell expectations ({expectations.horizon}-day hold)
        </h3>
        <p className="mt-0.5 text-xs text-text-faint">
          What following this cohort&rsquo;s methodology has historically felt like, by market phase at
          entry — descriptive history only, never a forecast or a promise.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-sm" data-testid="evidence-expectations-table">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
              <th className="py-1.5 pr-3 font-medium">Phase</th>
              <th className="py-1.5 pr-3 text-right font-medium">Max-DD depth</th>
              <th className="py-1.5 pr-3 text-right font-medium">Underwater</th>
              <th className="py-1.5 pr-3 text-right font-medium">Time to recover</th>
              <th className="py-1.5 text-right font-medium">Longest losing streak</th>
            </tr>
          </thead>
          <tbody>
            {expectations.by_phase.map((row) => (
              <tr key={row.phase} className="border-b border-border last:border-b-0" data-testid="evidence-expectations-phase-row">
                <td className="py-1.5 pr-3">
                  <Badge variant="default">{row.phase}</Badge>
                </td>
                <td className="py-1.5 pr-3 text-right">
                  <DistributionCellView cell={row.max_drawdown} format={fmtMdd} />
                </td>
                <td className="py-1.5 pr-3 text-right">
                  <DistributionCellView cell={row.underwater_days} format={formatDays} />
                </td>
                <td className="py-1.5 pr-3 text-right">
                  <DistributionCellView cell={row.time_to_recover_days} format={formatDays} />
                </td>
                <td className="py-1.5 text-right">
                  <LossStreakCellView cell={row.loss_streak} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-faint" data-testid="evidence-expectations-method-note">
        {expectations.method_note}
      </p>
      <p className="text-xs text-text-faint" data-testid="evidence-expectations-survivorship">
        {expectations.survivorship_bias}
      </p>
    </div>
  );
}

/** One median/p90/n distribution cell — "insufficient (n=…)" below the server's honesty floor (never a
 *  fabricated distribution), otherwise the median with the p90 + n alongside. `format` re-displays a
 *  served number only (never computes one) — the SAME `fmtMdd`/`formatDays` helpers other evidence
 *  surfaces already use. */
function DistributionCellView({
  cell,
  format,
}: {
  cell: DistributionCell;
  format: (value: number | null | undefined) => string;
}) {
  if (cell.insufficient) {
    return <span className="num text-text-faint">{insufficientLabel(cell.n)}</span>;
  }
  return (
    <span className="num text-text">
      {format(cell.median)} <span className="text-text-faint">(p90 {format(cell.p90)})</span>{" "}
      <span className="text-text-faint">n={cell.n}</span>
    </span>
  );
}

/** The longest-losing-streak cell — "insufficient (n=…)" below the (independent, smaller) streak floor,
 *  otherwise the streak length + the cadence-date count it was counted over. */
function LossStreakCellView({ cell }: { cell: LossStreakCell }) {
  if (cell.insufficient) {
    return <span className="num text-text-faint">{insufficientLabel(cell.n)}</span>;
  }
  return (
    <span className="num text-text">
      {formatStreak(cell.value)} <span className="text-text-faint">(n={cell.n})</span>
    </span>
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
