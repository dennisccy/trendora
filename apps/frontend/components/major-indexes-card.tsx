"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, LineChart } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { IndexRegimeChart } from "@/components/index-regime-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";
import { usePersistedToggle } from "@/lib/use-persisted-toggle";
import {
  fetchIndexes,
  fetchRegimeHistory,
  type IndexesResponse,
  type RegimePoint,
} from "@/lib/api";

/**
 * J-44 dashboard "Major indexes & regime" card. It renders normalized-% index lines (server-computed,
 * config-listed symbols) over soft stored-regime background bands, with a config-driven range-preset
 * switcher and an enable toggle (default ON, persisted client-side, fully hides the card when off).
 *
 * Single source of truth: the % series come from `GET /api/indexes` (computed server-side) and the
 * regime bands from `GET /api/regime-history` (stored labels/scores) — both at the SAME as-of, so a
 * historical global as-of renders no bar and no band dated after D. The frontend recomputes nothing.
 */
export function MajorIndexesCard() {
  const { asOf } = useAsOf();
  // The enable toggle is a client display preference (default ON, persisted) — when OFF the card is
  // fully hidden except a compact "show" affordance so the user can bring it back.
  const [enabled, setEnabled] = usePersistedToggle("trendora.dashboard.indexCard", true);
  // The selected range-preset key (null ⇒ the server's config default). Range options come from the API.
  const [rangeKey, setRangeKey] = useState<string | null>(null);
  const [indexes, setIndexes] = useState<IndexesResponse | null>(null);
  const [regimePoints, setRegimePoints] = useState<RegimePoint[]>([]);
  const [status, setStatus] = useState<"loading" | "ok" | "empty" | "error">("loading");

  useEffect(() => {
    if (!enabled) return; // don't fetch while hidden
    const controller = new AbortController();
    setStatus("loading");
    const asof = asOf ?? undefined;
    Promise.all([
      fetchIndexes(rangeKey ?? undefined, asof, controller.signal),
      fetchRegimeHistory(asof, controller.signal).catch(() => ({ asof_date: "", points: [] as RegimePoint[] })),
    ])
      .then(([ix, rh]) => {
        setIndexes(ix);
        setRegimePoints(rh.points);
        setStatus(ix.series.length > 0 ? "ok" : "empty");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      });
    return () => controller.abort();
  }, [enabled, rangeKey, asOf]);

  // When OFF, fully hide the card (J-44) but keep a small inline control to re-enable it.
  if (!enabled) {
    return (
      <button
        type="button"
        onClick={() => setEnabled(true)}
        className={cn(
          "flex items-center gap-2 rounded-md border border-dashed border-border bg-surface px-3 py-2 text-xs text-text-muted",
          "transition-colors hover:border-border-strong hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        )}
      >
        <LineChart className="h-4 w-4" aria-hidden />
        Show Major indexes &amp; regime
      </button>
    );
  }

  const ranges = indexes?.ranges ?? [];
  const activeRange = indexes?.range.key ?? rangeKey ?? "";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <CardTitle>Major indexes &amp; regime</CardTitle>
          {indexes ? (
            <span className="num text-xs text-text-faint">as of {formatIsoDate(indexes.asof_date)}</span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          {ranges.length > 0 ? (
            <Select
              aria-label="Range preset"
              value={activeRange}
              onChange={(event) => setRangeKey(event.target.value)}
              className="h-8 w-24 text-xs"
            >
              {ranges.map((range) => (
                <option key={range.key} value={range.key}>
                  {range.label}
                </option>
              ))}
            </Select>
          ) : null}
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            onClick={() => setEnabled(false)}
            className={cn(
              "rounded border border-border-strong bg-surface-2 px-2.5 py-1 text-xs text-text",
              "transition-colors hover:text-text focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            )}
          >
            Hide
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {status === "loading" ? (
          <div className="h-80 w-full animate-pulse rounded bg-surface-2" />
        ) : null}
        {status === "ok" && indexes ? (
          <IndexRegimeChart
            series={indexes.series}
            regimePoints={regimePoints}
            asofDate={indexes.asof_date}
          />
        ) : null}
        {status === "empty" ? (
          <div className="flex h-80 flex-col items-center justify-center gap-2 text-sm text-text-muted">
            <LineChart className="h-8 w-8 text-text-faint" aria-hidden />
            <p>No index history is available for this range.</p>
            <p className="text-xs text-text-faint">
              Configured index ETFs without stored bars are omitted honestly — nothing is fabricated.
            </p>
          </div>
        ) : null}
        {status === "error" ? (
          <div className="flex h-80 items-center gap-3 rounded border border-warn bg-surface p-5 text-sm text-warn">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Index chart unavailable</p>
              <p className="text-text-muted">
                The normalized index series could not load from the API. Nothing is fabricated — confirm
                the backend is running and reload.
              </p>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
