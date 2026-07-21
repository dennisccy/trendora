"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Layers, LineChart } from "lucide-react";

import { useAsOf } from "@/components/asof-provider";
import { PhaseCrossViewChart } from "@/components/phase-cross-view-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { cn } from "@/lib/utils";
import { usePersistedToggle } from "@/lib/use-persisted-toggle";
import {
  fetchIndexes,
  fetchMarketPhase,
  fetchRegimeHistory,
  type IndexesResponse,
  type MarketPhaseResponse,
  type RegimePoint,
} from "@/lib/api";

/**
 * J-97 Dashboard cross-view card — hosts the two-pane synced chart directly below the J-44 "Major indexes
 * & regime" card. It fetches the SAME canonical sources, all in FULL mode (display-only context past the
 * as-of marker):
 *   - `GET /api/indexes?full=true`        — the normalized-% index lines (both panes plot these).
 *   - `GET /api/regime-history?full=true` — the stored-regime bands (top pane, the J-44 lens).
 *   - `GET /api/market-phase?full=true`   — the full-history causal phase timeline (bottom pane: phase
 *     bands + the 0–100 severity line + the filtered P(bear) line), read VERBATIM (no client math).
 *
 * Single source of truth: the bottom pane's phase/severity/P(bear) are the SAME served market-phase series
 * the Market-Phase card reads (the card shows the bounded tail; this reads the full series) — no second
 * computation, no second endpoint. Exactly one date selector (J-18): the synced two-pane zoom is a view
 * transform, NOT a second date state — this card holds NO date `useState` and adds NO keydown listener;
 * it re-points only with the single global as-of from `useAsOf()`.
 *
 * iter-6 (J-06): this card's 3-request `Promise.all` fetch is DEFERRED by `FETCH_STAGGER_MS` after mount
 * instead of firing immediately. Real-browser measurement (iter-5 dev handoff, reconfirmed by browser-qa)
 * found `GET /api/indexes?full=true` queued behind Chrome's 6-connections-per-origin cap when this card's
 * fetch fired the instant the page mounted, alongside the initial Next.js asset burst — 1.68-2.19s
 * real-browser vs a ≤1.5s budget, even though curl's own baseline (0.79-0.95s) was comfortably under it.
 * The deferral is pure request TIMING: the same 3 calls, same states, same `AbortController` cleanup —
 * only WHEN they fire changes. The skeleton (`status === "loading"`, set synchronously before the
 * deferral) covers the whole deferred window, so there is never a blank gap.
 */
const FETCH_STAGGER_MS = 250;

export function PhaseCrossViewCard() {
  const { asOf, isHistorical } = useAsOf();
  const [enabled, setEnabled] = usePersistedToggle("trendora.dashboard.phaseCrossView", true);
  const [indexes, setIndexes] = useState<IndexesResponse | null>(null);
  const [regimePoints, setRegimePoints] = useState<RegimePoint[]>([]);
  const [phase, setPhase] = useState<MarketPhaseResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "empty" | "error">("loading");

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    setStatus("loading");
    const asof = asOf ?? undefined;
    // iter-6 (J-06): stagger this card's on-mount fetch burst behind the page's own initial same-origin
    // connection burst (see the module-level comment above) — the skeleton above already covers this
    // window, so the deferral is invisible except for when the network calls actually fire.
    const timer = window.setTimeout(() => {
      Promise.all([
        // full history on every source so the whole market path is the synced context (J-49 precedent).
        fetchIndexes(undefined, asof, controller.signal, true),
        fetchRegimeHistory(asof, controller.signal, true).catch(
          () => ({ asof_date: "", points: [] as RegimePoint[] }),
        ),
        // J-97: the full-history causal phase timeline (retrospective=false, full=true).
        fetchMarketPhase(asof, controller.signal, false, true),
      ])
        .then(([ix, rh, mp]) => {
          setIndexes(ix);
          setRegimePoints(rh.points);
          setPhase(mp);
          setStatus(ix.series.length > 0 ? "ok" : "empty");
        })
        .catch(() => {
          if (!controller.signal.aborted) setStatus("error");
        });
    }, FETCH_STAGGER_MS);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [enabled, asOf]);

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
        <Layers className="h-4 w-4" aria-hidden />
        Show regime × phase cross-view
      </button>
    );
  }

  const timelineFull = phase?.timeline_full ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <CardTitle className="flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-text-faint" aria-hidden />
            Regime × phase cross-view
          </CardTitle>
          {indexes ? (
            <span className="num text-xs text-text-faint">as of {formatIsoDate(indexes.asof_date)}</span>
          ) : null}
        </div>
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
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-xs text-text-muted">
          The same index path under two lenses on one synchronized chart — the stored-regime bands (top) and
          the market-phase bands + 0–100 severity + zero-centered severity-velocity line (bottom; positive =
          stress worsening). Zoom or drag either pane to re-range both; the vertical marker shows the as-of
          date (context past it is display-only). Hover for the regime label/score, phase, severity, P(bear),
          and severity-velocity at that date.
        </p>
        {status === "loading" ? (
          <div className="h-[28rem] w-full animate-pulse rounded bg-surface-2" />
        ) : null}
        {status === "ok" && indexes ? (
          <PhaseCrossViewChart
            series={indexes.series}
            regimePoints={regimePoints}
            timeline={timelineFull}
            asofDate={indexes.asof_date}
            isHistorical={isHistorical}
          />
        ) : null}
        {status === "empty" ? (
          <div className="flex h-[28rem] flex-col items-center justify-center gap-2 text-sm text-text-muted">
            <LineChart className="h-8 w-8 text-text-faint" aria-hidden />
            <p>No index history is available for this date.</p>
            <p className="text-xs text-text-faint">
              The cross-view renders nothing rather than fabricating a path — confirm data is loaded.
            </p>
          </div>
        ) : null}
        {status === "error" ? (
          <div className="flex h-[28rem] items-center gap-3 rounded border border-warn bg-surface p-5 text-sm text-warn">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Cross-view unavailable</p>
              <p className="text-text-muted">
                The index or market-phase series could not load from the API. Nothing is fabricated — confirm
                the backend is running and reload.
              </p>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
