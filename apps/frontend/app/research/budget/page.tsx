"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { PageHeading } from "@/components/page-heading";
import { Card, CardContent } from "@/components/ui/card";
import { fetchBudget, type BudgetResponse, type BudgetSpendPoint } from "@/lib/api";
import { formatPValue } from "@/lib/evidence";
import { cn } from "@/lib/utils";

/**
 * /research/budget — the certification-budget accounting panel (goal-mcp-loop iter-32, J-17 / backlog
 * B-903).
 *
 * A read-only view of how much statistical-credibility budget has already been spent, BEFORE any new
 * scan is proposed: total canonical trials to date, the current canonical `required_p` bar, the
 * Thresholdout budget remaining, and the staging LORD++ next-trial level — each with a per-trial
 * spend-over-time trend. Reads ONLY `GET /api/research/budget`, which re-reads (or re-derives via the
 * SAME referee/ledger seams the certifier uses) the exact accounting `app.mcp.tools:verify_edge`
 * consumes — nothing is recomputed here. No forms, no mutations.
 *
 * NO proven-language anywhere on this page: every figure is descriptive accounting (a trial count, a
 * significance bar, an alpha budget) — never a "Proven"/"Not yet proven" signal. The single source of
 * "Proven" stays `/evidence`; this page never resolves or displays evidence status.
 */
export default function BudgetPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchBudget(controller.signal)
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
          title="Certification-budget accounting"
          subtitle="How much statistical-credibility budget has already been spent, before any new scan is proposed — re-read from the same referee/ledger accounting the certifier uses. Descriptive accounting only; nothing here is a proven/not-proven signal."
        />
      </div>

      {state.kind === "loading" ? <BudgetSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The budget accounting panel could not load from the API. Confirm the backend is running
              and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? <BudgetGrid data={state.data} /> : null}
    </div>
  );
}

type State = { kind: "loading" } | { kind: "ok"; data: BudgetResponse } | { kind: "error" };

/** A same-window link back to the Research hub (mirrors `research/graveyard/page.tsx`'s pattern exactly). */
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

/** Budget figures are always in [0, 1] (a fraction of the starting alpha budget). 4 significant figures
 *  mirrors `formatPValue`'s own precision (both are bar-like probabilities on this panel), but a budget
 *  amount can legitimately BE exactly 0 ("fully spent") — so, unlike `formatPValue`, 0 renders as "0",
 *  never the p-value-style "< 0.0001" wording. Display-only; never recomputed. */
function formatAlpha(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  if (value <= 0) return "0";
  return Number(value.toPrecision(4)).toString();
}

function BudgetGrid({ data }: { data: BudgetResponse }) {
  const { canonical, staging } = data;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="budget-grid">
      <StatCard
        testId="budget-trials"
        title="Total trials to date"
        headline={String(canonical.n_trials_to_date)}
        subtext={`Next canonical trial will be #${canonical.n_trials_next}`}
        sparkline={<Sparkline values={canonical.spend_over_time.map((p) => p.trial)} />}
      />
      <StatCard
        testId="budget-required-p"
        title="Current canonical required p"
        headline={formatPValue(canonical.required_p)}
        subtext={`= ${canonical.alpha_per_test} ÷ ${canonical.n_trials_next} (Bonferroni)`}
        sparkline={<Sparkline values={spendField(canonical.spend_over_time, "required_p")} />}
      />
      <StatCard
        testId="budget-thresholdout-remaining"
        title="Thresholdout budget remaining"
        headline={formatAlpha(canonical.alpha_budget_remaining)}
        subtext={`of ${formatAlpha(canonical.alpha_budget_total)} total · spent ${formatAlpha(canonical.alpha_spent)}`}
        sparkline={<Sparkline values={spendField(canonical.spend_over_time, "alpha_charged")} />}
      />
      <StatCard
        testId="budget-staging-wealth"
        title="Staging LORD++ next-trial level"
        headline={formatPValue(staging.next_level)}
        subtext={`trial #${staging.n_trials_next} of the internal staging economy`}
        sparkline={<Sparkline values={spendField(staging.spend_over_time, "required_p")} />}
      />
    </div>
  );
}

/** Pull one numeric field off a spend-over-time series for the sparkline, defensively skipping any
 *  point missing that field (never fabricating a 0 in its place). */
function spendField(points: BudgetSpendPoint[], field: "required_p" | "alpha_charged"): number[] {
  return points
    .map((p) => p[field])
    .filter((v): v is number => typeof v === "number" && Number.isFinite(v));
}

function StatCard({
  testId,
  title,
  headline,
  subtext,
  sparkline,
}: {
  testId: string;
  title: string;
  headline: string;
  subtext: string;
  sparkline: React.ReactNode;
}) {
  return (
    <Card data-testid={testId}>
      <CardContent className="space-y-3 p-5">
        <h3 className="text-xs font-medium uppercase tracking-wide text-text-faint">{title}</h3>
        <p className="num text-2xl font-semibold text-text" data-testid={`${testId}-value`}>
          {headline}
        </p>
        <p className="text-xs text-text-muted">{subtext}</p>
        {sparkline}
      </CardContent>
    </Card>
  );
}

/** A compact per-metric spend-over-time mini-trend — an inline SVG sparkline (no charting library; 4
 *  small series don't warrant one). Pure presentation: `values` are already-fetched, verbatim/re-derived
 *  server numbers in append order; this only maps them to normalized pixel coordinates for the polyline
 *  — no new statistic is computed, exactly like any chart library's own internal pixel scaling. An empty
 *  series (0 trials on that ledger) renders an honest placeholder, never a crash. */
function Sparkline({ values }: { values: number[] }) {
  if (values.length === 0) {
    return (
      <div className="flex h-8 items-center text-[11px] text-text-faint" data-testid="budget-sparkline-empty">
        No trials yet
      </div>
    );
  }
  const width = 120;
  const height = 32;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1; // a flat series (min === max) still renders a level line, never divides by 0
  const coords = values.map((v, i) => {
    const x = values.length === 1 ? width / 2 : (i / (values.length - 1)) * width;
    const y = height - ((v - min) / span) * (height - 4) - 2;
    return { x, y };
  });
  const points = coords.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-8 w-full text-accent"
      preserveAspectRatio="none"
      role="img"
      aria-label="spend-over-time trend"
      data-testid="budget-sparkline"
    >
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} />
      {coords.map(({ x, y }, i) => (
        <circle key={i} cx={x} cy={y} r={1.5} fill="currentColor" />
      ))}
    </svg>
  );
}

function BudgetSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" data-testid="budget-skeleton">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="p-5">
          <div className="space-y-3">
            <div className={cn("h-3 w-24 animate-pulse rounded bg-surface-2")} />
            <div className={cn("h-7 w-16 animate-pulse rounded bg-surface-2")} />
            <div className={cn("h-8 w-full animate-pulse rounded bg-surface-2")} />
          </div>
        </Card>
      ))}
    </div>
  );
}
