"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Disclosure } from "@/components/ui/disclosure";
import { formatIsoDate } from "@/lib/dates";
import { stockResidualDisclosureText, stockShownCapDisclosureText } from "@/lib/stock-accounting-summary";
import type { CompassResponse, SessionDeltaChange } from "@/lib/api";

const KIND_LABEL: Record<SessionDeltaChange["kind"], string> = {
  market: "Market",
  breadth: "Breadth",
  sector: "Sector",
  theme: "Theme",
  stock: "Stock",
};

/** J-02 (goal-market-compass iter-2): the What-changed card. Every entry, its ordering, and its
 *  threshold gate are all decided server-side (`app.engine.session_delta`) — this component only
 *  re-displays the served `session_delta` block; it computes no threshold and no diff. */
export function CompassWhatChangedCard({ compass }: { compass: CompassResponse | null }) {
  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-whatchanged-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        What-changed is unavailable — backend not reachable.
      </Card>
    );
  }

  const { session_delta } = compass;
  const noPriorRun = session_delta.prior_as_of === null;
  // goal-market-compass iter-40 (J-15): both `null` when `session_delta.stock_accounting` is absent (a
  // manifest frozen before this field existed) -- the card then renders nothing new, exactly as before
  // this iteration (AG-8).
  const stockCapText = stockShownCapDisclosureText(session_delta.stock_accounting);
  const stockResidualText = stockResidualDisclosureText(session_delta.stock_accounting);

  return (
    <Card data-testid="compass-whatchanged-card">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>What changed</CardTitle>
        {!noPriorRun ? (
          <span className="text-xs text-text-muted" data-testid="compass-whatchanged-prior">
            vs {formatIsoDate(session_delta.prior_as_of)} ({session_delta.gap_days}{" "}
            day{session_delta.gap_days === 1 ? "" : "s"} ago)
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-3">
        {noPriorRun ? (
          <p className="text-sm text-text-muted" data-testid="compass-whatchanged-no-prior">
            This is the earliest stored session — there is no prior session to compare against.
          </p>
        ) : session_delta.changes.length === 0 ? (
          <p className="text-sm text-text-muted" data-testid="compass-whatchanged-quiet">
            No meaningful changes this session.
          </p>
        ) : (
          <ul className="space-y-2" data-testid="compass-whatchanged-list">
            {session_delta.changes.map((change, index) => (
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
        {/* goal-market-compass iter-40 (J-15, TC-4b): discloses its own bound instead of truncating
            silently -- only when the display cap actually held something back this session. */}
        {stockCapText !== null ? (
          <p className="text-xs text-text-faint" data-testid="compass-whatchanged-stock-cap">
            {stockCapText}
          </p>
        ) : null}
        <Disclosure summary={`Suppressed moves (${session_delta.suppressed_count})`}>
          {session_delta.suppressed.length === 0 ? (
            <p className="pt-1 text-xs text-text-faint">No moves were suppressed this session.</p>
          ) : (
            <ul className="space-y-1 pt-1" data-testid="compass-suppressed-list">
              {session_delta.suppressed.map((entry, index) => (
                <li key={index} className="flex items-center justify-between gap-2 text-xs text-text-muted">
                  <span>{KIND_LABEL[entry.kind as SessionDeltaChange["kind"]] ?? entry.kind}</span>
                  <span className="num">
                    {entry.magnitude.toFixed(2)} &lt; {entry.threshold.toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Disclosure>
        {/* goal-market-compass iter-40 (J-15, TC-4): a residual disclosure, VISIBLY DISTINCT from the
            "Suppressed moves" line above -- an above-threshold mover held back by the display cap is a
            different thing from a below-threshold one; count only, no per-name list (AG-8). Renders only
            when `session_delta.stock_accounting` is present (absent on manifests frozen before this field
            existed, TC-5); shows an explicit zero rather than nothing when nothing was held back. */}
        {stockResidualText !== null ? (
          <p className="text-xs text-text-muted" data-testid="compass-whatchanged-stock-residual">
            {stockResidualText}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
