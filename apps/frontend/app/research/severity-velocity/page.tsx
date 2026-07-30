"use client";

import { useEffect, useState } from "react";

import { ShieldAlert } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { fmtPct, returnClass } from "@/components/forward-return";
import { Card } from "@/components/ui/card";
import { SampleLink } from "@/components/sample-link";
import { cn } from "@/lib/utils";
import {
  fetchSeverityVelocity,
  type SeverityVelocityResponse,
  type SeverityVelocityCell,
} from "@/lib/api";
import { Microscope } from "lucide-react";

import {
  HorizonSelector,
  LabSkeleton,
  ResearchCaveat,
  ResearchControls,
  ResearchError,
  SlowComputeNotice,
  useElapsedSeconds,
  useResearchControls,
} from "../_labs";
// ops-hardening iter-36 (J-06): `resolveLabLoadPanel` is not re-exported from `_labs.tsx` (it is imported
// there, not re-exported) — sourced directly from its own module, the same way `_labs.tsx` itself does.
import { resolveLabLoadPanel } from "@/lib/lab-load-panel";
import { WarmingState, shouldShowWarming } from "@/components/warming-state";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: SeverityVelocityResponse }
  | { kind: "error" };

/** Format a win-rate fraction (0.5 -> "50%"); null/NA renders an em dash. Not a return, so no +/- sign. */
function fmtWinRate(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}

/** /research/severity-velocity (J-103) — the Severity-velocity × Regime forward-return study on its own
 *  lazy route (reached from the /research hub, J-104). The regime-family × velocity-sign matrix of the
 *  stored benchmark (SPY) forward return — mean / win-rate / N per cell — defaulting to the all-history
 *  aggregate and honoring the shared As-of mode (J-32). Re-formats server-computed figures only; it
 *  computes no return / velocity / regime itself (No recompute in the read path). */
export default function SeverityVelocityPage() {
  const [horizon, setHorizon] = useState<number | undefined>(undefined);
  const [state, setState] = useState<State>({ kind: "loading" });
  const { mode, setMode, readiness, asofCutoff, scope } = useResearchControls();
  // ops-hardening iter-36 (J-06): a manual re-fetch counter — the SAME `attempt` pattern Regime Lab already
  // proved (iter-33, UT-11), so a genuine backend-unavailable condition gets a working Retry instead of a
  // frozen error card.
  const [attempt, setAttempt] = useState(0);
  const elapsedSeconds = useElapsedSeconds(state.kind === "loading");

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchSeverityVelocity(horizon, asofCutoff ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [horizon, asofCutoff, readiness, attempt]);

  const data = state.kind === "ok" ? state.data : null;
  const selectedHorizon = horizon ?? data?.horizon;
  // ops-hardening iter-36 (J-06): the SAME honest pre-data state Regime Lab already renders
  // (lib/lab-load-panel.ts) — a brief load stays a plain skeleton; a wait past the grace window becomes an
  // explicit, time-stamped "still computing" notice; a failure becomes a retryable error card.
  const panel = resolveLabLoadPanel(state.kind, elapsedSeconds);

  return (
    <div className="space-y-4">
      <ResearchControls
        title="Research — Severity-velocity × Regime"
        subtitle="Does rising or falling stress under a given regime predict the market's next move? A regime-family × velocity-sign matrix of the benchmark (SPY) forward return — mean, win-rate, and N per horizon — grouped once from the stored forward returns. Descriptive evidence, never a forecast."
        mode={mode}
        onModeChange={setMode}
        asofCutoff={asofCutoff}
        controls={
          <HorizonSelector
            horizons={data?.horizons ?? []}
            value={selectedHorizon}
            onChange={(h) => setHorizon(h)}
          />
        }
      />

      <ResearchCaveat
        survivorship={data?.survivorship_bias}
        descriptive={data?.descriptive_caveat}
      />

      {shouldShowWarming(readiness) ? (
        <WarmingState what="The Severity-velocity × Regime study" />
      ) : (
        <>
          {panel.kind === "computing" ? (
            <SlowComputeNotice
              what="The Severity-velocity × Regime study"
              elapsedSeconds={panel.elapsedSeconds}
            />
          ) : null}
          {panel.kind === "skeleton" || panel.kind === "computing" ? <LabSkeleton /> : null}
          {panel.kind === "error" ? (
            <ResearchError
              what="The Severity-velocity × Regime study"
              onRetry={() => setAttempt((previous) => previous + 1)}
            />
          ) : null}
          {data ? <SeverityVelocityBody data={data} scope={scope} /> : null}
        </>
      )}
    </div>
  );
}

/** The matrix + the plain-language verdict. Re-formats the served figures only. */
function SeverityVelocityBody({
  data,
  scope,
}: {
  data: SeverityVelocityResponse;
  scope: "all" | "asof";
}) {
  const horizon = data.horizon;
  return (
    <Card className="p-0" data-testid="severity-velocity-section">
      <div className="border-b border-border p-4">
        <h2 className="text-base font-semibold text-text">
          Severity-velocity × Regime — forward {data.benchmark} return ({horizon}d)
        </h2>
        <p className="mt-1 text-sm text-text-muted">
          Conditioned on the regime family (rows) and the sign of severity-velocity (columns) at each
          snapshot date, the mean forward {data.benchmark} return, win-rate, and sample size N — a read-only
          grouping of the stored forward returns by the served severity-velocity (J-102) + stored regime
          label. Cells with n &lt; {data.min_sample} show NA + n, never a fabricated number.
        </p>
      </div>

      {data.n_total === 0 ? (
        <div className="p-4">
          <EmptyState
            icon={Microscope}
            title="No forward-tested observations for this horizon"
            description="No stored snapshot has a benchmark forward return and a derivable severity-velocity at this horizon. Pick a shorter horizon or widen the as-of window — no cohort is fabricated to fill the gap."
          />
        </div>
      ) : (
        <div className="overflow-x-auto p-4">
          <table className="w-full border-collapse text-sm" data-testid="severity-velocity-matrix">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                <th className="py-2 pr-3 font-medium">Regime family</th>
                {data.velocity_signs.map((sign) => (
                  <th key={sign.key} className="px-3 py-2 text-right font-medium">
                    {sign.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.matrix.map((row) => (
                <tr key={row.family} className="border-b border-border/60 last:border-0">
                  <td className="py-3 pr-3 font-medium text-text">{row.family_label}</td>
                  {row.cells.map((cell) => (
                    <td key={cell.velocity_sign} className="px-3 py-3 text-right align-top">
                      <MatrixCell
                        cell={cell}
                        family={row.family}
                        horizon={horizon}
                        minSample={data.min_sample}
                        scope={scope}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <SeverityVelocityVerdict caveat={data.verdict_caveat} />
    </Card>
  );
}

/** One matrix cell: the mean forward return (colored) + win-rate + the count-coherent N= chip (new tab).
 *  A low-sample / empty cell shows NA honestly (the engine already gated mean/win-rate to null). */
function MatrixCell({
  cell,
  family,
  horizon,
  minSample,
  scope,
}: {
  cell: SeverityVelocityCell;
  family: string;
  horizon: number;
  minSample: number;
  scope: "all" | "asof";
}) {
  const { stats } = cell;
  // a cell below min_sample is shown as NA + n (never a fabricated mean) — matching the other labs' gating.
  const showFigures = stats.n >= minSample;
  return (
    <div className="inline-flex flex-col items-end gap-1">
      <span className={cn("num font-semibold", showFigures ? returnClass(stats.mean_return) : "text-text-muted")}>
        {showFigures ? fmtPct(stats.mean_return) : "NA"}
      </span>
      <span className="num text-xs text-text-muted">
        {showFigures ? `win ${fmtWinRate(stats.win_rate)}` : "low sample"}
      </span>
      <SampleLink
        n={stats.n}
        min={minSample}
        scope={scope}
        cohort={{
          kind: "severity-velocity",
          horizon,
          family,
          velocitySign: cell.velocity_sign,
        }}
        label={`Open the ${family} · ${cell.velocity_sign_label} cohort (n=${stats.n}) in Research Samples (new tab)`}
      />
    </div>
  );
}

/** The plain-language verdict + the honest limitations VERBATIM (the hypothesis is NOT supported on this
 *  bull-dominated seed — surfaced exactly as the backend serves it; the frontend authors no conclusion). */
function SeverityVelocityVerdict({ caveat }: { caveat: string }) {
  return (
    <div className="border-t border-border p-4" data-testid="severity-velocity-verdict">
      <Card className="flex items-start gap-3 border-warn bg-surface p-4 text-sm">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-warn" aria-hidden />
        <div className="space-y-1">
          <p className="font-medium text-warn">Verdict &amp; honest limitations</p>
          <p className="text-text-muted">{caveat}</p>
        </div>
      </Card>
    </div>
  );
}
