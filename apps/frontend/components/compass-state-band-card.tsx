"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { useAsOfHref } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Disclosure } from "@/components/ui/disclosure";
import { phaseColor } from "@/lib/phase";
import { regimeVariant } from "@/lib/regime-variant";
import type { CompassResponse, DashboardResponse, MarketPhaseResponse } from "@/lib/api";

/** Phase label → Badge palette variant (same posture grouping used elsewhere for this exact field —
 *  presentation only, no threshold evaluated here). */
function phaseBadgeVariant(phase: string | null): "ok" | "warn" | "danger" {
  if (phase === "Bear" || phase === "Correction") return "danger";
  if (phase === "Pullback") return "warn";
  return "ok";
}

/** One direction-word badge for a `state_band.<band>` entry. `word === null` covers every honest
 *  no-comparison case (no prior run, a missing per-band input, backend/compass unreachable, or a
 *  manifest minted before `state_band` existed) with the SAME explicit "NA" — never a fabricated
 *  direction (AG-3). */
function DirectionBadge({ word, testId }: { word: string | null | undefined; testId: string }) {
  return (
    <Badge variant="default" className="num" data-testid={testId}>
      {word ?? "NA"}
    </Badge>
  );
}

/** J-07 (goal-market-compass iter-28): the market-state band — the first section of the Today page's
 *  ten-second read. Regime tile (label + score from `GET /api/dashboard`, direction word from
 *  `state_band.regime`) and phase tile (phase + severity + P(bear) from `GET /api/market-phase`,
 *  direction word from `state_band.stress`) each carry a breakdown disclosure reusing the shared
 *  `ComponentBreakdown` against their canonical endpoint's `components` array, plus the breadth level +
 *  direction word (`state_band.breadth`) from the SAME `GET /api/dashboard` payload. Every value shown
 *  is a served field — this component evaluates no threshold and selects no word.
 *
 *  `dashboard` is REQUIRED (the page only renders this card once `GET /api/dashboard` has succeeded);
 *  `phase` and `compass` degrade independently and honestly — a null `phase` or `compass` (or a
 *  `compass.state_band` that is `null`, e.g. a manifest minted before this field existed) never
 *  fabricates a value, it renders the same explicit NA/unavailable state that surface already uses. */
export function CompassStateBandCard({
  dashboard,
  phase,
  compass,
}: {
  dashboard: DashboardResponse;
  phase: MarketPhaseResponse | null;
  compass: CompassResponse | null;
}) {
  const asofHref = useAsOfHref();
  const stateBand = compass?.state_band ?? null;
  const { regime, breadth } = dashboard;

  return (
    <Card data-testid="compass-state-band-card">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Market state</CardTitle>
        <Link
          href={asofHref("/market")}
          data-testid="compass-state-band-market-link"
          className="inline-flex items-center gap-1 text-xs text-accent hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
        >
          Full market context (regime × phase, sectors, themes)
          <ArrowRight className="h-3 w-3" aria-hidden />
        </Link>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          {/* Regime tile — GET /api/dashboard's regime.label/score, direction word from state_band.regime */}
          <div className="space-y-3 rounded-md border border-border p-4" data-testid="compass-state-band-regime-tile">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-text">Regime</span>
              <Badge variant={regimeVariant(regime.label)}>{regime.label}</Badge>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="num text-3xl font-semibold text-text">{regime.score.toFixed(2)}</span>
              <span className="text-xs text-text-muted">/ 100</span>
              <DirectionBadge word={stateBand?.regime.direction_word} testId="compass-state-band-regime-direction" />
            </div>
            <Disclosure summary="Why this regime — component breakdown">
              <ComponentBreakdown components={regime.components} className="pt-1" />
            </Disclosure>
          </div>

          {/* Phase tile — GET /api/market-phase's phase/severity/p_bear, direction word from state_band.stress */}
          <div className="space-y-3 rounded-md border border-border p-4" data-testid="compass-state-band-phase-tile">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-text">Market phase</span>
              {phase && phase.available && phase.phase ? (
                <Badge variant={phaseBadgeVariant(phase.phase)}>{phase.phase}</Badge>
              ) : null}
            </div>
            {phase === null ? (
              <p className="text-sm text-neg">Market-phase data unavailable — backend not reachable.</p>
            ) : !phase.available ? (
              <p className="text-sm text-text-muted">
                Not enough history to derive a market phase for this date — reported NA, never fabricated.
              </p>
            ) : (
              <>
                <div className="flex items-baseline gap-2">
                  <span
                    className="num text-3xl font-semibold"
                    style={{ color: phase.phase ? phaseColor(phase.phase) : undefined }}
                  >
                    {phase.severity != null ? phase.severity.toFixed(2) : "NA"}
                  </span>
                  <span className="text-xs text-text-muted">/ 100 severity</span>
                  <DirectionBadge word={stateBand?.stress.direction_word} testId="compass-state-band-stress-direction" />
                </div>
                <p className="num text-xs text-text-muted">
                  P(bear) {phase.p_bear != null ? phase.p_bear.toFixed(2) : "NA"}
                </p>
                <Disclosure summary="Why this severity — component breakdown">
                  <ComponentBreakdown components={phase.components} className="pt-1" />
                </Disclosure>
              </>
            )}
          </div>
        </div>

        {/* Breadth — GET /api/dashboard's breadth level, direction word from state_band.breadth. No
            breakdown disclosure: /api/dashboard's breadth block carries no `components` array. */}
        <div
          className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border p-3 text-sm"
          data-testid="compass-state-band-breadth"
        >
          <span className="text-text-muted">
            Breadth ·{" "}
            <span className="num text-text">
              {breadth.above_50dma_pct != null ? `${breadth.above_50dma_pct.toFixed(1)}%` : "NA"}
            </span>{" "}
            above 50-DMA
          </span>
          <DirectionBadge word={stateBand?.breadth.direction_word} testId="compass-state-band-breadth-direction" />
        </div>
      </CardContent>
    </Card>
  );
}
