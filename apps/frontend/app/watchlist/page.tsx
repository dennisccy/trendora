"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Plus, Star, Trash2 } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  addWatchlistEntry,
  fetchWatchlist,
  removeWatchlistEntry,
  type WatchlistEntry,
  type WatchlistResponse,
} from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: WatchlistResponse }
  | { kind: "error" };

/** Format a return fraction (0.0123 -> "+1.23%"); null = NA (no entry_close / no current close). */
function fmtPct(value: number | null): string {
  if (value === null || value === undefined) return "NA";
  const pct = value * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

/** Positive green, negative red, zero/NA muted — palette tokens only (DESIGN SYSTEM). */
function priceClass(value: number | null): string {
  if (value === null || value === undefined) return "text-text-muted";
  if (value > 0) return "text-pos";
  if (value < 0) return "text-neg";
  return "text-text";
}

function setupVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "Actionable":
      return "ok";
    case "Breakout-watch":
    case "Pullback-watch":
      return "accent";
    case "Extended":
    case "Risk-off-watchlist":
      return "warn";
    case "Avoid":
      return "danger";
    default:
      return "default";
  }
}

// Form controls reuse the Select component's palette tokens (h-9, rounded, border, surface-2,
// accent focus ring) so the Add panel matches the dense-dark workstation style.
const FIELD =
  "h-9 rounded-md border border-border bg-surface-2 px-3 text-sm text-text placeholder:text-text-faint " +
  "transition-colors hover:border-border-strong focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent " +
  "disabled:cursor-not-allowed disabled:opacity-50";

export default function WatchlistPage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [ticker, setTicker] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  function load(signal?: AbortSignal) {
    fetchWatchlist(signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch(() => {
        if (!signal?.aborted) setState({ kind: "error" });
      });
  }

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    const symbol = ticker.trim().toUpperCase();
    if (!symbol || busy) return;
    setBusy(true);
    setActionError(null);
    try {
      await addWatchlistEntry(symbol, reason.trim());
      setTicker("");
      setReason("");
      load(); // refresh the list from the server (single source — never optimistic)
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not add to the watchlist.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(id: number) {
    if (busy) return;
    setBusy(true);
    setActionError(null);
    try {
      await removeWatchlistEntry(id);
      load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not remove the entry.");
    } finally {
      setBusy(false);
    }
  }

  const entries: WatchlistEntry[] = state.kind === "ok" ? state.data.entries : [];

  return (
    <div className="space-y-4">
      <PageHeading
        title="Watchlist"
        subtitle="Your saved stocks — each shows its current Leadership / Entry / Risk, setup, price-since-added and invalidation, read live from the scanner. A research save-list, persisted across restarts."
      />

      {/* Add panel — the product's first user-write action (a save-list, not an order) */}
      <Card className="p-4">
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Ticker
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. ANET"
              aria-label="Ticker to add"
              autoCapitalize="characters"
              spellCheck={false}
              className={cn(FIELD, "num w-32")}
            />
          </label>
          <label className="flex flex-1 flex-col gap-1 text-xs text-text-muted">
            Reason
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why are you watching it?"
              aria-label="Reason for watching"
              className={cn(FIELD, "w-full min-w-48")}
            />
          </label>
          <button
            type="submit"
            disabled={busy || !ticker.trim()}
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-bg",
              "transition hover:brightness-110 active:brightness-95",
              "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            <Plus className="h-4 w-4" aria-hidden />
            Add
          </button>
        </form>
        {actionError ? (
          <p role="alert" className="mt-3 flex items-center gap-2 text-sm text-neg">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
            {actionError}
          </p>
        ) : null}
      </Card>

      {state.kind === "loading" ? <WatchlistSkeleton /> : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              The watchlist could not load from the API. No entries are shown rather than fabricated
              values. Confirm the backend is running and retry.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" && entries.length === 0 ? (
        <EmptyState
          icon={Star}
          title="Your watchlist is empty"
          description="Add a ticker above with your own reason. Each saved stock shows its date added, your reason, current Leadership / Entry / Risk and setup, price-since-added and an invalidation level — and persists across a backend restart."
        />
      ) : null}

      {state.kind === "ok" && entries.length > 0 ? (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="default" className="num">
              as of {state.data.asof_date}
            </Badge>
            <span className="num text-xs text-text-faint">{entries.length} saved</span>
          </div>
          <Card className="overflow-x-auto p-0">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-text-faint">
                  <th className="px-3 py-2 font-medium">Ticker</th>
                  <th className="px-3 py-2 font-medium">Added</th>
                  <th className="px-3 py-2 font-medium">Reason</th>
                  <th className="px-3 py-2 font-medium">Leadership</th>
                  <th className="px-3 py-2 font-medium">Entry Quality</th>
                  <th className="px-3 py-2 font-medium">Risk</th>
                  <th className="px-3 py-2 font-medium">Setup</th>
                  <th className="px-3 py-2 font-medium">Since added</th>
                  <th className="px-3 py-2 font-medium">Invalidation</th>
                  <th className="px-3 py-2 font-medium">
                    <span className="sr-only">Remove</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <WatchlistRow key={entry.id} entry={entry} onRemove={handleRemove} busy={busy} />
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function WatchlistRow({
  entry,
  onRemove,
  busy,
}: {
  entry: WatchlistEntry;
  onRemove: (id: number) => void;
  busy: boolean;
}) {
  return (
    <tr className="border-b border-border align-top transition-colors hover:bg-surface-2">
      <td className="px-3 py-2">
        <Link
          href={`/stocks/${entry.ticker}`}
          className="num font-semibold text-accent hover:underline focus-visible:underline focus-visible:outline-none"
        >
          {entry.ticker}
        </Link>
      </td>
      <td className="num px-3 py-2 text-xs text-text-muted">{entry.date_added.slice(0, 10)}</td>
      <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
        <span className="line-clamp-2" title={entry.reason}>
          {entry.reason || <span className="text-text-faint">—</span>}
        </span>
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={entry.leadership.bucket} score={entry.leadership.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={entry.entry_quality.bucket} score={entry.entry_quality.score} />
      </td>
      <td className="px-3 py-2">
        <ScoreBadge bucket={entry.risk.bucket} score={entry.risk.score} invert />
      </td>
      <td className="px-3 py-2">
        <Badge variant={setupVariant(entry.setup.status)}>{entry.setup.status}</Badge>
      </td>
      <td className={cn("num px-3 py-2 font-medium", priceClass(entry.price_since_added))}>
        {fmtPct(entry.price_since_added)}
      </td>
      <td className="max-w-xs px-3 py-2 text-xs text-text-muted">
        <span className="line-clamp-2" title={entry.invalidation.note}>
          {entry.invalidation.note}
        </span>
      </td>
      <td className="px-3 py-2 text-right">
        <button
          type="button"
          onClick={() => onRemove(entry.id)}
          disabled={busy}
          aria-label={`Remove ${entry.ticker} from the watchlist`}
          className={cn(
            "inline-flex h-8 w-8 items-center justify-center rounded-md border border-border text-text-muted",
            "transition-colors hover:border-neg hover:text-neg",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          <Trash2 className="h-4 w-4" aria-hidden />
        </button>
      </td>
    </tr>
  );
}

function WatchlistSkeleton() {
  return (
    <Card className="space-y-2 p-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-8 w-full animate-pulse rounded bg-surface-2" />
      ))}
    </Card>
  );
}
