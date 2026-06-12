"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, History } from "lucide-react";

import { useAsOfHref } from "@/components/asof-provider";
import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { fetchRuns, type RunSummary, type RunsResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: RunsResponse }
  | { kind: "error" };

/** Colour-graded regime badge (palette tokens only): risk-on green, risk-off/defensive red,
 *  the in-between regimes amber. Matches the Dashboard's regime colouring. */
function regimeVariant(label: string): "ok" | "warn" | "danger" | "default" {
  if (label === "Strong risk-on" || label === "Risk-on") return "ok";
  if (label === "Defensive" || label === "Risk-off") return "danger";
  return "warn"; // Narrow leadership · Choppy
}

export default function ScannerRunsPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchRuns(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="space-y-4">
      <PageHeading
        title="Scanner Runs"
        subtitle="History of immutable, dated scan snapshots — open one to see exactly what the scanner said on that date"
      />

      {state.kind === "loading" ? <RunsSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The scan-run history could not load from the API. No runs are shown rather than
              fabricated values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && state.data.runs.length === 0 ? (
        <EmptyState
          icon={History}
          title="No scanner runs yet"
          description="Each scan is saved as an immutable, dated snapshot. Runs appear here once the scanner has persisted at least one snapshot."
        />
      ) : null}

      {state.kind === "ok" && state.data.runs.length > 0 ? (
        <Card className="overflow-x-auto p-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="px-3 py-2 font-medium">As of</th>
                <th className="px-3 py-2 font-medium">Regime</th>
                <th className="px-3 py-2 text-right font-medium">Actionable</th>
                <th className="px-3 py-2 text-right font-medium">Breakout-watch</th>
                <th className="px-3 py-2 text-right font-medium">Pullback-watch</th>
                <th className="px-3 py-2 text-right font-medium">Stocks</th>
              </tr>
            </thead>
            <tbody>
              {state.data.runs.map((run) => (
                <RunTableRow key={run.run_id} run={run} />
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}

function RunTableRow({ run }: { run: RunSummary }) {
  const asofHref = useAsOfHref();
  const counts = run.candidate_counts;
  return (
    <tr className="border-b border-border transition-colors hover:bg-surface-2">
      <td className="px-3 py-2">
        <Link
          href={asofHref(`/scanner-runs/${run.run_id}`)}
          className="num font-semibold text-accent hover:underline focus-visible:underline focus-visible:outline-none"
        >
          {formatIsoDate(run.asof_date)}
        </Link>
      </td>
      <td className="px-3 py-2">
        <span className="inline-flex items-center gap-2">
          <Badge variant={regimeVariant(run.regime.label)}>{run.regime.label}</Badge>
          <span className="num text-xs text-text-muted">{run.regime.score.toFixed(2)}</span>
        </span>
      </td>
      <td className="num px-3 py-2 text-right text-pos">{counts["Actionable"] ?? 0}</td>
      <td className="num px-3 py-2 text-right text-text">{counts["Breakout-watch"] ?? 0}</td>
      <td className="num px-3 py-2 text-right text-text">{counts["Pullback-watch"] ?? 0}</td>
      <td className="num px-3 py-2 text-right text-text-muted">{run.n_stocks}</td>
    </tr>
  );
}

function RunsSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
