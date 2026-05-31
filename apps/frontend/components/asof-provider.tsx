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
}

const AsOfContext = createContext<AsOfContextValue | null>(null);

export function AsOfProvider({ children }: { children: React.ReactNode }) {
  const [dates, setDates] = useState<string[]>([]);
  const [latest, setLatest] = useState<string | null>(null);
  const [asOf, setAsOfState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    fetchRuns()
      .then((res) => {
        if (!active) return;
        const ordered = res.runs.map((run) => run.asof_date); // already descending by as-of date
        setDates(ordered);
        setLatest(ordered[0] ?? null);
        setReady(true);
      })
      .catch(() => {
        // /api/runs unavailable → degrade to latest-only (the switcher disables; pages use latest)
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  // Selecting the latest date (or null) is the "current" view — normalise it to null so the
  // historical indicator never shows for the latest date.
  const setAsOf = useCallback(
    (date: string | null) => setAsOfState(date && date !== latest ? date : null),
    [latest],
  );

  const isHistorical = asOf !== null && asOf !== latest;

  const value = useMemo<AsOfContextValue>(
    () => ({ asOf, setAsOf, latest, dates, isHistorical, ready }),
    [asOf, setAsOf, latest, dates, isHistorical, ready],
  );

  return <AsOfContext.Provider value={value}>{children}</AsOfContext.Provider>;
}

/** Read the global as-of state. Must be used within `<AsOfProvider>` (mounted in the app shell). */
export function useAsOf(): AsOfContextValue {
  const ctx = useContext(AsOfContext);
  if (!ctx) throw new Error("useAsOf must be used within <AsOfProvider>");
  return ctx;
}
