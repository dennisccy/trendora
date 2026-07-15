import { cn } from "@/lib/utils";
import type { WatchlistXray } from "@/lib/api";

/**
 * J-23 (backlog B-204) — the pairwise return-correlation matrix inside the watchlist X-ray.
 *
 * READ-ONLY presentation of `xray.correlation_matrix`, served verbatim by `GET /api/watchlist` — NO
 * browser-side correlation recompute (B-204's named dominant failure mode). Cells reuse the app's
 * EXISTING sign tokens (`text-pos` / `text-neg` / muted), the SAME family `price_since_added` already
 * uses on this page — never a new color scale. An undefined/insufficient-history pair renders an
 * honest NA cell (`—`, muted, dashed border) rather than a fabricated number.
 */

function fmtCorr(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(2);
}

function cellTextClass(value: number | null): string {
  if (value === null || value === undefined) return "text-text-faint";
  if (value > 0) return "text-pos";
  if (value < 0) return "text-neg";
  return "text-text-muted";
}

function cellTitle(rowTicker: string, colTicker: string, value: number | null, xray: WatchlistXray): string {
  if (rowTicker === colTicker) {
    return `${rowTicker}: ${xray.history_days[rowTicker] ?? 0} of ${xray.window_days} trailing days available`;
  }
  if (value === null) {
    const rowDays = xray.history_days[rowTicker] ?? 0;
    const colDays = xray.history_days[colTicker] ?? 0;
    return (
      `${rowTicker} vs ${colTicker}: not enough overlapping history for a correlation ` +
      `(${rowTicker}: ${rowDays}d, ${colTicker}: ${colDays}d of the trailing ${xray.window_days}d window; ` +
      `need >= ${xray.min_overlap_days}d each)`
    );
  }
  return `${rowTicker} vs ${colTicker}: ${value.toFixed(3)} correlation over the trailing ${xray.window_days} trading days`;
}

export function CorrelationHeatmap({ xray }: { xray: WatchlistXray }) {
  const { tickers, correlation_matrix } = xray;
  return (
    <div className="overflow-x-auto" data-testid="watchlist-xray-matrix">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            <th className="px-2 py-1 text-left">
              <span className="sr-only">Ticker</span>
            </th>
            {tickers.map((ticker) => (
              <th key={ticker} className="num px-2 py-1 text-center font-medium text-text-muted">
                {ticker}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickers.map((rowTicker) => (
            <tr key={rowTicker}>
              <th scope="row" className="num px-2 py-1 text-left font-medium text-text-muted">
                {rowTicker}
              </th>
              {tickers.map((colTicker) => {
                const value = correlation_matrix[rowTicker]?.[colTicker] ?? null;
                const isSelf = rowTicker === colTicker;
                return (
                  <td
                    key={colTicker}
                    data-testid="watchlist-xray-cell"
                    data-row={rowTicker}
                    data-col={colTicker}
                    data-na={value === null ? "yes" : "no"}
                    title={cellTitle(rowTicker, colTicker, value, xray)}
                    className={cn(
                      "num border px-2 py-1 text-center tabular-nums",
                      isSelf ? "bg-surface-2" : "bg-surface",
                      value === null ? "border-dashed border-border" : "border-border",
                      cellTextClass(value),
                    )}
                  >
                    {fmtCorr(value)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
