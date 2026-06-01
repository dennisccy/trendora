"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { fetchRuns } from "@/lib/api";

/**
 * Global as-of date state (iter-8, J-13). A single client context, mounted in the app shell so it
 * SURVIVES client-side navigation (selecting a date on `/` keeps it on `/stocks`, `/themes`, …
 * without rewriting every sidebar/row link). It only tracks WHICH stored date the as-of-aware pages
 * fetch — it computes no score/bucket/return; the backend serves those from the immutable snapshot.
 *
 * Available dates come from the canonical immutable run list (`GET /api/runs`); the default is the
 * latest. If the list can't load, the switcher degrades to latest-only (no crash, never fabricated).
 */
export interface AsOfContextValue {
  /** The selected historical date (YYYY-MM-DD), or null when viewing the latest. */
  asOf: string | null;
  /** Select a historical date, or null/the latest date to return to the current view. */
  setAsOf: (date: string | null) => void;
  /** The latest available run date (the default view), or null before the list loads. */
  latest: string | null;
  /** All available run dates, descending (newest first) — the switcher's options. */
  dates: string[];
  /** True when a historical date (≠ latest) is selected — drives the "(historical)" indicator. */
  isHistorical: boolean;
  /** True once the run list has been fetched (or failed) — the switcher is disabled until then. */
  ready: boolean;
  /** Re-fetch the canonical run list (`GET /api/runs`) so dates created since mount (e.g. by a Data
   *  Manager backfill) become selectable WITHOUT a hard reload. Additive + non-disruptive: it only
   *  refreshes the available `dates`/`latest`; it never changes the user's current `asOf` selection. */
  refresh: () => void;
}

const AsOfContext = createContext<AsOfContextValue | null>(null);

export function AsOfProvider({ children }: { children: React.ReactNode }) {
  const [dates, setDates] = useState<string[]>([]);
  const [latest, setLatest] = useState<string | null>(null);
  const [asOf, setAsOfState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // Single canonical loader for the run list. The mount effect runs it (with an abort guard); the
  // exposed `refresh()` re-runs it on demand (e.g. after a Data Manager job creates new snapshots).
  // It only updates the AVAILABLE dates/latest — it never touches the user's `asOf` selection, so a
  // refresh that adds OLDER dates leaves `latest` (and the current view) exactly as they were.
  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const res = await fetchRuns(signal);
      const ordered = res.runs.map((run) => run.asof_date); // already descending by as-of date
      setDates(ordered);
      setLatest(ordered[0] ?? null);
      setReady(true);
    } catch {
      // /api/runs unavailable or aborted → degrade to latest-only (the switcher disables; pages use latest)
      if (!signal?.aborted) setReady(true);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const refresh = useCallback(() => {
    void load();
  }, [load]);

  // Selecting the latest date (or null) is the "current" view — normalise it to null so the
  // historical indicator never shows for the latest date.
  const setAsOf = useCallback(
    (date: string | null) => setAsOfState(date && date !== latest ? date : null),
    [latest],
  );

  const isHistorical = asOf !== null && asOf !== latest;

  const value = useMemo<AsOfContextValue>(
    () => ({ asOf, setAsOf, latest, dates, isHistorical, ready, refresh }),
    [asOf, setAsOf, latest, dates, isHistorical, ready, refresh],
  );

  return <AsOfContext.Provider value={value}>{children}</AsOfContext.Provider>;
}

/** Read the global as-of state. Must be used within `<AsOfProvider>` (mounted in the app shell). */
export function useAsOf(): AsOfContextValue {
  const ctx = useContext(AsOfContext);
  if (!ctx) throw new Error("useAsOf must be used within <AsOfProvider>");
  return ctx;
}
