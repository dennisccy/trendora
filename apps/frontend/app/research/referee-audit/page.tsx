"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, ShieldAlert, ShieldCheck } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { fetchRefereeAudit, type RefereeAuditReport, type RefereeAuditResponse } from "@/lib/api";
import { formatIsoDate } from "@/lib/dates";
import { formatPValue } from "@/lib/evidence";
import { cn } from "@/lib/utils";

/**
 * /research/referee-audit — the referee-calibration report (goal-mcp-loop iter-36, J-22 / backlog
 * B-102).
 *
 * A read-only view of whether the certifier itself is calibrated: the empirical false-pass rate (with a
 * binomial CI) measured over seeded null (label-permuted) factors against the configured significance
 * level α, plus a lookahead-contaminated-factor tripwire result — all computed ONCE by an ISOLATED
 * offline job against a throwaway ledger (the real certified-claims/staging ledgers and the real
 * Thresholdout budget are never touched) and re-read VERBATIM here. Reads ONLY
 * `GET /api/research/referee-audit`; no forms, no mutations, no UI action triggers the audit run.
 *
 * NO proven-language anywhere on this page: every figure is descriptive calibration accounting (a trial
 * count, a false-pass rate, a verdict kind) — never a "Proven"/"Not yet proven" signal. The single source
 * of "Proven" stays `/evidence`; this page never resolves or displays evidence status, and the audit's
 * own throwaway trials never appear on that ledger.
 */
export default function RefereeAuditPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchRefereeAudit(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <BackToResearch />
        <PageHeading
          title="Referee audit"
          subtitle="Is the certifier itself calibrated? The measured empirical false-pass rate over seeded null factors, against the configured significance level, plus a lookahead-contaminated-factor tripwire — computed once by an isolated offline job against a throwaway ledger. Descriptive calibration accounting only; nothing here is a proven/not-proven signal."
        />
      </div>

      {state.kind === "loading" ? <RefereeAuditSkeleton /> : null}

      {state.kind === "error" ? (
        <Card
          className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg"
          data-testid="referee-audit-error"
        >
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The referee-audit report could not load from the API. Confirm the backend is running and
              reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? <ReportBody report={state.data.report} /> : null}
    </div>
  );
}

type State = { kind: "loading" } | { kind: "ok"; data: RefereeAuditResponse } | { kind: "error" };

/** A same-window link back to the Research hub (mirrors `research/budget/page.tsx`'s pattern exactly). */
function BackToResearch() {
  const asofHref = useAsOfHref();
  return (
    <Link
      href={asofHref("/research")}
      className="inline-flex items-center gap-1 text-xs font-medium text-text-muted hover:text-accent focus-visible:text-accent focus-visible:outline-none"
    >
      <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> Back to Research
    </Link>
  );
}

function ReportBody({ report }: { report: RefereeAuditReport | null }) {
  if (report === null) {
    return <EmptyState />;
  }
  if (report.status === "unreadable") {
    return <UnreadableState />;
  }
  return <ReportPanel report={report} />;
}

/** The honest empty state — no offline harness run has ever persisted an artifact yet. The audit is a
 *  config-seeded job, not a UI action, so this page never offers a "run it" button (J-22 is read-only). */
function EmptyState() {
  return (
    <Card data-testid="referee-audit-empty">
      <CardContent className="space-y-3 p-6">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-text-faint" aria-hidden />
          <h2 className="text-sm font-semibold text-text">No audit run yet</h2>
        </div>
        <p className="max-w-2xl text-sm text-text-muted">
          The referee-calibration harness has not been run yet. It runs as a config-seeded offline job
          (<code className="rounded bg-surface-2 px-1 py-0.5 text-xs">python -m app.engine.referee_audit</code>),
          never as a UI action here — once it runs, its persisted report appears on this page.
        </p>
      </CardContent>
    </Card>
  );
}

/** An artifact exists but could not be parsed — an honest degraded read, distinct from "never run"
 *  (EmptyState) and distinct from the tripwire failure (this is a data-integrity hiccup, not a caught
 *  leak). Amber, not red — mirrors `DriftReportPanel`'s own unreadable-artifact treatment on /data. */
function UnreadableState() {
  return (
    <Card className="border-warn bg-warn/10" data-testid="referee-audit-unreadable">
      <CardContent className="flex items-start gap-3 p-6">
        <AlertTriangle className="h-5 w-5 shrink-0 text-warn" aria-hidden />
        <div>
          <p className="font-medium text-warn">Audit artifact unreadable</p>
          <p className="text-text-muted">
            A referee-audit report exists but could not be parsed. Re-run the offline harness
            (<code className="rounded bg-surface-2 px-1 py-0.5 text-xs">python -m app.engine.referee_audit</code>)
            to regenerate it.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/** The verdict-kind badge variant — mirrors `research/graveyard/page.tsx`'s `verdictKindVariant` mapping
 *  for FAIL/INSUFFICIENT. A PASS here is the tripwire-fired case (the contaminated factor slipped
 *  through) — mapped to `danger`, NEVER `accent` (this page must never render a "Proven"-looking badge,
 *  anti-goal #1), since a PASS on the perfect-crime factor is alarming, not a proof of anything. */
function contaminatedStatusVariant(status: string | null | undefined): "danger" | "warn" | "default" {
  if (status === "FAIL" || status === "PASS") return "danger";
  if (status === "INSUFFICIENT") return "warn";
  return "default";
}

function ReportPanel({ report }: { report: RefereeAuditReport }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="referee-audit-grid">
        <StatCard
          testId="referee-audit-null-trials"
          title="Null trials"
          headline={String(report.n_null_trials ?? "—")}
          subtext={`source factor: ${report.source_factor ?? "—"}`}
        />
        <StatCard
          testId="referee-audit-false-pass-rate"
          title="Empirical false-pass rate"
          headline={formatPValue(report.false_pass_rate)}
          subtext={`${report.false_pass_count ?? "—"} of ${report.n_null_trials ?? "—"} trials · 95% CI [${formatPValue(report.false_pass_ci_low)}, ${formatPValue(report.false_pass_ci_high)}]`}
        />
        <StatCard
          testId="referee-audit-alpha"
          title="Configured α"
          headline={formatPValue(report.alpha)}
          subtext="the significance level the null trials are judged against"
        />
        <StatCard
          testId="referee-audit-run-date"
          title="Run date"
          headline={formatIsoDate(report.run_date)}
          subtext={`seed ${report.seed ?? "—"} · contaminated horizon ${report.contaminated_factor_horizon ?? "—"}d`}
        />
      </div>

      {report.contaminated_caught ? (
        <CalmContaminatedCard report={report} />
      ) : (
        <TripwireCard report={report} />
      )}
    </div>
  );
}

/** The calm, quiet treatment — the contaminated "perfect crime" factor was correctly rejected (or ruled
 *  insufficient), exactly as expected. Styling stays consistent with the rest of the evidence-status
 *  language: unremarkable, never celebratory hype. */
function CalmContaminatedCard({ report }: { report: RefereeAuditReport }) {
  const status = report.contaminated_verdict?.status ?? null;
  return (
    <Card data-testid="referee-audit-contaminated-caught">
      <CardContent className="space-y-2 p-5">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-pos" aria-hidden />
          <h3 className="text-sm font-semibold text-text">Lookahead-contaminated factor: caught</h3>
        </div>
        <p className="text-sm text-text-muted">
          A factor whose value equals its own realized {report.contaminated_factor_horizon ?? "—"}-day
          forward return (the &quot;perfect crime&quot; a broken harness would certify instantly) was
          submitted to the referee — expected: {report.contaminated_expected_outcome ?? "rejected"}.
          Verdict:{" "}
          <Badge variant={contaminatedStatusVariant(status)} data-testid="referee-audit-contaminated-status">
            {status ?? "—"}
          </Badge>
          .
        </p>
        {report.contaminated_verdict?.reason ? (
          <p className="text-xs text-text-faint">{String(report.contaminated_verdict.reason)}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

/** The LOUD, un-hideable failure state — the contaminated factor was NOT rejected. This is a
 *  correctness-critical signal (the harness may be leaking), never decoration: prominent red, always
 *  rendered when `contaminated_caught` is false, never suppressed or softened. */
function TripwireCard({ report }: { report: RefereeAuditReport }) {
  const status = report.contaminated_verdict?.status ?? null;
  return (
    <Card className="border-neg bg-neg/10" data-testid="referee-audit-tripwire">
      <CardContent className="flex items-start gap-3 p-6">
        <AlertTriangle className="h-6 w-6 shrink-0 text-neg" aria-hidden />
        <div className="space-y-1.5">
          <h3 className="text-base font-semibold text-neg">
            Tripwire: the lookahead-contaminated factor was NOT rejected
          </h3>
          <p className="text-sm text-neg">
            A factor whose value equals its own realized {report.contaminated_factor_horizon ?? "—"}-day
            forward return should have been rejected by the referee (expected:{" "}
            {report.contaminated_expected_outcome ?? "rejected"}) — instead it certified{" "}
            <Badge variant={contaminatedStatusVariant(status)} data-testid="referee-audit-contaminated-status">
              {status ?? "—"}
            </Badge>
            . This means the certification harness may be leaking signal it should not — treat every
            certified claim from this basis with suspicion until this is investigated.
          </p>
          {report.contaminated_verdict?.reason ? (
            <p className="text-xs text-neg/80">{String(report.contaminated_verdict.reason)}</p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function StatCard({
  testId,
  title,
  headline,
  subtext,
}: {
  testId: string;
  title: string;
  headline: string;
  subtext: string;
}) {
  return (
    <Card data-testid={testId}>
      <CardContent className="space-y-2 p-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-text-faint">{title}</h3>
        <p className="num text-2xl font-semibold text-text" data-testid={`${testId}-value`}>
          {headline}
        </p>
        <p className="text-xs text-text-muted">{subtext}</p>
      </CardContent>
    </Card>
  );
}

function RefereeAuditSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="referee-audit-skeleton">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="p-5">
          <div className="space-y-3">
            <div className={cn("h-3 w-24 animate-pulse rounded bg-surface-2")} />
            <div className={cn("h-7 w-16 animate-pulse rounded bg-surface-2")} />
            <div className={cn("h-3 w-full animate-pulse rounded bg-surface-2")} />
          </div>
        </Card>
      ))}
    </div>
  );
}
