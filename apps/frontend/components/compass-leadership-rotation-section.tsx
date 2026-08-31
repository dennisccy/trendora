"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CompassResponse, SessionDeltaChange } from "@/lib/api";

const ROTATION_KINDS: readonly SessionDeltaChange["kind"][] = ["sector", "theme", "stock"];

const KIND_LABEL: Record<SessionDeltaChange["kind"], string> = {
  market: "Market",
  breadth: "Breadth",
  sector: "Sector",
  theme: "Theme",
  stock: "Stock",
};

/** J-07 (goal-market-compass iter-28): the Leadership rotation section — a presentational, kind-filtered
 *  slice of the ALREADY-served `session_delta.changes` array (`GET /api/compass`, the existing J-02
 *  Data-Contract row). No new computed value, no client-side threshold or word selection — this
 *  component only filters the served list to `kind ∈ {sector, theme, stock}` for display; the market-
 *  and breadth-kind entries stay in the What-changed card above, unfiltered. */
export function CompassLeadershipRotationSection({ compass }: { compass: CompassResponse | null }) {
  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-leadership-rotation-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        Leadership rotation is unavailable — backend not reachable.
      </Card>
    );
  }

  const entries = compass.session_delta.changes.filter((change) => ROTATION_KINDS.includes(change.kind));

  return (
    <Card data-testid="compass-leadership-rotation-section">
      <CardHeader>
        <CardTitle>Leadership rotation</CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-text-muted" data-testid="compass-leadership-rotation-empty">
            No sector, theme, or stock rotation this session.
          </p>
        ) : (
          <ul className="space-y-2" data-testid="compass-leadership-rotation-list">
            {entries.map((change, index) => (
              <li key={`${change.kind}-${index}`} className="flex items-start justify-between gap-3 text-sm">
                <span className="flex flex-wrap items-center gap-2">
                  <Badge variant="default">{KIND_LABEL[change.kind]}</Badge>
                  <Link href={change.drill_href} className="text-text hover:underline">
                    {change.label}
                  </Link>
                </span>
                <span className="num shrink-0 text-xs text-text-muted">
                  {String(change.from)} &rarr; {String(change.to)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
