"use client";

import {
  createContext,
  Suspense,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { fetchRuns } from "@/lib/api";
import { isValidIsoDate } from "@/lib/dates";

/**
 * Global as-of date state (iter-8, J-13). A single client context, mounted in the app shell so it
 * SURVIVES client-side navigation (selecting a date on `/` keeps it on `/stocks`, `/themes`, …
 * without rewriting every sidebar/row link). It only tracks WHICH stored date the as-of-aware pages
 * fetch — it computes no score/bucket/return; the backend serves those from the immutable snapshot.
 *
 * Available dates come from the canonical immutable run list (`GET /api/runs`); the default is the
 * latest. If the list can't load, the switcher degrades to latest-only (no crash, never fabricated).
 *
 * J-43 (deep-linkable as-of): the ONE global state is SERIALIZED into the URL as `?asof=yyyy-MM-dd`
 * while a historical date is selected (and the URL is date-free at latest). On load, a URL carrying
 * `?asof` is restored INTO this one global control. The URL is the serialization of the single state —
 * this provider is the ONLY reader/writer of the param; no page parses or holds its own date state.
 * An unknown/invalid `?asof` (malformed, or a date with no run) degrades safely to the latest view.
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

/** The single URL query key that serializes the global as-of state (J-43). One name, one owner. */
const ASOF_PARAM = "asof";

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

  return (
    <AsOfContext.Provider value={value}>
      {/* J-43 URL↔state sync lives in its own component behind a Suspense boundary because it reads
          `useSearchParams()` (an App-Router requirement). It renders nothing — it only restores a
          deep-linked `?asof` into this one control on load and serializes the state back to the URL.
          It sits INSIDE the provider so it can use the context; the app `children` are unaffected. */}
      <Suspense fallback={null}>
        <AsOfUrlSync
          asOf={asOf}
          dates={dates}
          latest={latest}
          ready={ready}
          setAsOf={setAsOf}
        />
      </Suspense>
      {children}
    </AsOfContext.Provider>
  );
}

/**
 * The single reader/writer of the `?asof` URL param (J-43). It does two things, both through the ONE
 * global control:
 *  1. RESTORE on load: once the run list is `ready`, if the URL carries `?asof=D` and D is a valid,
 *     KNOWN historical run date, it selects it. A malformed value, the latest date, or a date with no
 *     run is ignored — degrading to the latest view (no crash, no fabricated date). It also strips a
 *     stale/invalid param from the URL so the URL stays an honest serialization of the resolved state.
 *  2. SERIALIZE on change: whenever the historical selection changes, it writes `?asof=D` (or removes
 *     the param at latest) via `router.replace` — no scroll jump, no history spam. It preserves any
 *     other query params untouched.
 * It renders nothing.
 */
function AsOfUrlSync({
  asOf,
  dates,
  latest,
  ready,
  setAsOf,
}: {
  asOf: string | null;
  dates: string[];
  latest: string | null;
  ready: boolean;
  setAsOf: (date: string | null) => void;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  // Restore the deep-linked param exactly once, after the run list is known (so "is D a real run?" can
  // be answered). Guards against a re-restore that would fight the user's later selection.
  const restored = useRef(false);

  // (1) Restore `?asof` into the one global control once the run list is ready.
  useEffect(() => {
    if (!ready || restored.current) return;
    restored.current = true;
    const raw = searchParams.get(ASOF_PARAM);
    if (!raw) return; // date-free URL → latest view (nothing to restore)
    // A valid, KNOWN historical run date restores; anything else (malformed, latest, or unknown date)
    // degrades to latest and the stale param is stripped below by the serialize effect.
    if (isValidIsoDate(raw) && raw !== latest && dates.includes(raw)) {
      setAsOf(raw);
    } else {
      // Strip the invalid/unknown param immediately so the URL doesn't keep lying about the state.
      writeAsofParam(router, pathname, searchParams, null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  // (2) Serialize the resolved state to the URL. Runs only AFTER the initial restore so it never races
  // the deep-link read. Historical → `?asof=D`; latest/null → the param is removed. Re-runs on
  // `pathname` too so a client-side nav (a leaderboard row `<Link>` → `/stocks/[ticker]`, which does
  // NOT carry query params) RE-ASSERTS `?asof` onto the new route — the historical view survives the
  // click-through (the provider, mounted in the shell, kept the state; this re-stamps the URL).
  useEffect(() => {
    if (!ready || !restored.current) return;
    const current = searchParams.get(ASOF_PARAM);
    const next = asOf && asOf !== latest ? asOf : null;
    // Avoid a redundant replace (and an effect loop) when the URL already matches the state.
    if ((current ?? null) === next) return;
    writeAsofParam(router, pathname, searchParams, next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asOf, latest, ready, pathname]);

  return null;
}

/** Write (or clear) exactly the `?asof` param on the current path, preserving all other query params.
 *  Uses `router.replace` with `scroll: false` so serialization never scrolls or spams history. */
function writeAsofParam(
  router: ReturnType<typeof useRouter>,
  pathname: string,
  searchParams: URLSearchParams,
  value: string | null,
) {
  const params = new URLSearchParams(searchParams.toString());
  if (value) params.set(ASOF_PARAM, value);
  else params.delete(ASOF_PARAM);
  const query = params.toString();
  router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
}

/** Read the global as-of state. Must be used within `<AsOfProvider>` (mounted in the app shell). */
export function useAsOf(): AsOfContextValue {
  const ctx = useContext(AsOfContext);
  if (!ctx) throw new Error("useAsOf must be used within <AsOfProvider>");
  return ctx;
}
