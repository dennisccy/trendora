"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { fetchIndexes, type IndexSeries } from "@/lib/api";

/**
 * iter-22 (J-14) — the index/benchmark/macro data-VENDOR disclosure panel on `/data`. Reads the SAME
 * canonical `GET /api/indexes` payload the Dashboard major-indexes chart reads (an additional reader,
 * NOT a re-parse of `meta.json` and NOT a new `/api/data` field — the Data Contract's single source of
 * truth for this value), and lists every rendered series' honest data vendor (Stooq / Yahoo /
 * FRED-macro proxy) alongside its real first-bar date. A series with no vendor record in the manifest
 * (the SPY/QQQ/IWM/RSP/DIA ETF lines) shows an honest "—", never a fabricated vendor; a FRED-macro-proxy
 * series reads as exactly that — never as a market index (anti-goal: a proxy must never be presented as
 * a real ticker).
 */
function PanelTitle({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="border-b border-border px-4 py-3">
      <h2 className="text-sm font-semibold text-text">{children}</h2>
      {hint ? <p className="mt-0.5 text-xs text-text-faint">{hint}</p> : null}
    </div>
  );
}

type State =
  | { kind: "loading" }
  | { kind: "ok"; series: IndexSeries[] }
  | { kind: "empty" }
  | { kind: "error" };

export function IndexVendorPanel() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    // full=true so this list matches every line the Dashboard chart can render (the same payload).
    fetchIndexes(undefined, undefined, controller.signal, true)
      .then((resp) => {
        setState(resp.series.length > 0 ? { kind: "ok", series: resp.series } : { kind: "empty" });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  return (
    <Card className="p-0" data-testid="index-vendor-panel">
      <PanelTitle hint="Every index/benchmark/macro line on the major-indexes chart, with its honest data vendor and real first-bar date — the same GET /api/indexes payload the Dashboard chart reads, never a recompute.">
        Index &amp; benchmark data provenance
      </PanelTitle>
      <div className="p-4">
        {state.kind === "loading" ? (
          <div className="h-24 w-full animate-pulse rounded bg-surface-2" data-testid="index-vendor-loading" />
        ) : null}
        {state.kind === "error" ? (
          <div className="flex items-center gap-3 rounded border border-warn bg-surface p-4 text-sm text-warn">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Vendor disclosure unavailable</p>
              <p className="text-text-muted">
                Could not load the index series from the API. Nothing is fabricated — confirm the backend
                is running and reload.
              </p>
            </div>
          </div>
        ) : null}
        {state.kind === "empty" ? (
          <p className="text-sm text-text-muted" data-testid="index-vendor-empty">
            No index series are available to disclose.
          </p>
        ) : null}
        {state.kind === "ok" ? (
          <div className="overflow-x-auto">
            <table data-testid="index-vendor-table" className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                  <th className="px-3 py-2 font-medium">Series</th>
                  <th className="px-3 py-2 font-medium">Vendor</th>
                  <th className="px-3 py-2 font-medium">First bar</th>
                </tr>
              </thead>
              <tbody>
                {state.series.map((s) => (
                  <tr
                    key={s.symbol}
                    className="border-b border-border last:border-b-0"
                    data-testid={`index-vendor-row-${s.symbol}`}
                  >
                    <td className="px-3 py-2 text-text">{s.name}</td>
                    <td className="px-3 py-2">
                      <Badge variant="default">{s.vendor ?? "—"}</Badge>
                    </td>
                    <td className="px-3 py-2 num text-text-muted">{formatIsoDate(s.first)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
