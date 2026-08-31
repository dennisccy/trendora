"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Clock } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { CompassStateBandCard } from "@/components/compass-state-band-card";
import { CompassSummaryCard } from "@/components/compass-summary-card";
import { CompassWhatChangedCard } from "@/components/compass-whatchanged-card";
import { CompassLeadershipRotationSection } from "@/components/compass-leadership-rotation-section";
import { CompassFocusSection } from "@/components/compass-focus-section";
import { CompassManifestStrip } from "@/components/compass-manifest-strip";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import {
  fetchCompass,
  fetchDashboard,
  fetchMarketPhase,
  type CompassResponse,
  type DashboardResponse,
  type MarketPhaseResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | {
      kind: "ok";
      dashboard: DashboardResponse;
      phase: MarketPhaseResponse | null;
      compass: CompassResponse | null;
    }
  | { kind: "error" };

/** J-07 (goal-market-compass iter-28): the Today page — the ten-second read, top to bottom: market-state
 *  band, summary, What changed, Leadership rotation, Next-session focus, manifest strip. The readiness
 *  badge + preflight strip stay in `layout.tsx` chrome, ABOVE this body (unchanged). `/` fetches ONLY
 *  `GET /api/dashboard`, `GET /api/market-phase`, and `GET /api/compass` on load — it no longer fetches
 *  `/api/sectors` or `/api/themes` (those moved to `/market`, J-08, where the former dashboard body now
 *  lives verbatim). */
export default function TodayPage() {
  const { asOf } = useAsOf();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const asof = asOf ?? undefined; // historical date or latest
    // Dashboard (regime + candidate counts) is critical; market-phase and compass read their own
    // canonical endpoints and may fail independently. All fetch the SAME as-of date so the snapshot
    // view is coherent across the page.
    setState({ kind: "loading" });
    fetchDashboard(asof, controller.signal)
      .then(async (dashboard) => {
        let phase: MarketPhaseResponse | null = null;
        let compass: CompassResponse | null = null;
        try {
          phase = await fetchMarketPhase(asof, controller.signal);
        } catch {
          phase = null;
        }
        try {
          compass = await fetchCompass(asof, controller.signal);
        } catch {
          compass = null;
        }
        setState({ kind: "ok", dashboard, phase, compass });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [asOf]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <PageHeading title="Today" subtitle="The ten-second read after the close" />
        {state.kind === "ok" ? (
          <Badge variant="default" className="num gap-1.5">
            <Clock className="h-3.5 w-3.5" aria-hidden />
            Data as-of {formatIsoDate(state.dashboard.asof_date)}
          </Badge>
        ) : null}
      </div>

      {state.kind === "loading" ? <TodaySkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The Today page could not load the market regime from the API. Nothing is fabricated —
              confirm the backend is running and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? (
        <>
          <CompassStateBandCard dashboard={state.dashboard} phase={state.phase} compass={state.compass} />
          <CompassSummaryCard compass={state.compass} />
          <CompassWhatChangedCard compass={state.compass} />
          <CompassLeadershipRotationSection compass={state.compass} />
          <CompassFocusSection compass={state.compass} />
          <CompassManifestStrip compass={state.compass} asOf={asOf} />
        </>
      ) : null}
    </div>
  );
}

function TodaySkeleton() {
  return (
    <div className="space-y-4">
      <Card className="h-56 animate-pulse bg-surface-2" />
      <Card className="h-32 animate-pulse bg-surface-2" />
      <Card className="h-48 animate-pulse bg-surface-2" />
      <Card className="h-40 animate-pulse bg-surface-2" />
      <Card className="h-64 animate-pulse bg-surface-2" />
      <Card className="h-48 animate-pulse bg-surface-2" />
    </div>
  );
}
