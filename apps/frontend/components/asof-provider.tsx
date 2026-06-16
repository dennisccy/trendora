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
import { canStepNext, canStepPrev, resolveStep } from "@/lib/asof-step";

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

/**
 * J-73 — read the deep-linked `?asof` date from the current URL SYNCHRONOUSLY, for the lazy initializer
 * of the ONE global as-of state (below). This is NOT a second date state: it only seeds the EXISTING
 * `asOf` `useState` on first mount so a `?asof=D` arrival's first data fetch is already at D (no
 * latest→D flash). It is shape-validated only (a real `yyyy-MM-dd`); the run-list `ready` step still
 * VALIDATES it against the known dates and degrades unknown/latest values to the latest view (J-43).
 *
 * Server-safe: during SSR `window` is undefined, so it returns null (the server cannot know the URL);
 * the client's lazy initializer then reads `window.location.search` on hydration. The asof-provider
 * remains the SOLE reader/writer of `?asof` — this is the same single owner reading the same one param.
 */
function readAsofFromUrl(): string | null {
  if (typeof window === "undefined") return null; // SSR: no URL to read yet → latest until client hydrates
  const raw = new URLSearchParams(window.location.search).get(ASOF_PARAM);
  // Only a well-formed ISO date is hydrated; anything else seeds null (→ latest) and, if present in the
  // URL, is stripped by the run-list validation step exactly as J-43 already does (no fabricated date).
  return raw && isValidIsoDate(raw) ? raw : null;
}

export function AsOfProvider({ children }: { children: React.ReactNode }) {
  const [dates, setDates] = useState<string[]>([]);
  const [latest, setLatest] = useState<string | null>(null);
  // J-73: hydrate the SINGLE global as-of state synchronously from `?asof` on first mount (a lazy
  // initializer on the EXISTING state — not a second date state) so a historical deep-link/reload/new-tab
  // renders at D from first paint with no latest→D flash. The run-list `ready` step below still validates
  // and degrades unknown/latest/malformed values to the latest view (J-43 unchanged).
  const [asOf, setAsOfState] = useState<string | null>(readAsofFromUrl);
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

  // (1) VALIDATE the synchronously-hydrated `?asof` against the one global control, once the run list is
  // ready. J-73: the state was already SEEDED from the URL on first mount (a lazy initializer on the one
  // `asOf` state — no second state), so the deep-linked page already fetched at D with no flash. This step
  // is now purely the J-43 validate/degrade pass: confirm D is a real historical run date, else degrade to
  // latest (reset the one state to null AND strip the stale param) — no fabricated date.
  useEffect(() => {
    if (!ready || restored.current) return;
    restored.current = true;
    const raw = searchParams.get(ASOF_PARAM);
    if (!raw) return; // date-free URL → latest view (nothing to restore/validate)
    // A valid, KNOWN historical run date is confirmed (setAsOf(raw) is a no-op when the lazy initializer
    // already seeded it). Anything else (malformed, the latest date, or an unknown date) degrades to
    // latest: reset the ONE state to null so a seeded-but-invalid date doesn't stick, and strip the param.
    if (isValidIsoDate(raw) && raw !== latest && dates.includes(raw)) {
      setAsOf(raw);
    } else {
      setAsOf(null); // J-73: undo a synchronously-seeded date that proved unknown/latest (J-43 degrade)
      writeAsofParam(router, pathname, searchParams, null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  // (2) Serialize the resolved state to the URL. Runs only AFTER the initial restore so it never races
  // the deep-link read. Historical → `?asof=D`; latest/null → the param is removed. Re-runs on
  // `pathname` too so a client-side nav (a leaderboard row `<Link>` → `/stocks/[ticker]`, which does
  // NOT carry query params) RE-ASSERTS `?asof` onto the new route — the historical view survives the
  // click-through (the provider, mounted in the shell, kept the state; this re-stamps the URL).
  //
  // J-43 FIX (iter-2): `searchParams` (via its stable `.toString()` key `searchKey`) is in the
  // dependency set. Without it, the closure captured a STALE `searchParams` on the deep-link path:
  // when `setAsOf(D)` committed `asOf=D`, this effect re-ran but still read the pre-restore URL
  // (`current === D === next`) and early-returned, so a date-free URL "won" permanently and the
  // `?asof=D` never got re-stamped after reload/fresh-tab. Keying on the LIVE URL lets the effect
  // re-evaluate against the URL Next.js actually committed, so the restored state serializes back.
  const searchKey = searchParams.toString();
  useEffect(() => {
    if (!ready || !restored.current) return;
    const current = searchParams.get(ASOF_PARAM);
    const next = asOf && asOf !== latest ? asOf : null;
    // Avoid a redundant replace (and an effect loop) when the URL already matches the state.
    if ((current ?? null) === next) return;
    writeAsofParam(router, pathname, searchParams, next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asOf, latest, ready, pathname, searchKey]);

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

/**
 * J-79 — step the ONE global as-of date one available snapshot at a time, bounded.
 *
 * The single hook every J-79 affordance uses (the top-bar ◀ ▶ buttons and the opt-in ← → keys): it reads
 * the same global state and drives the SAME `setAsOf` the calendar already calls — so stepping introduces
 * NO second/page-local date state and stays in sync with the `?asof` URL serialization (the provider stays
 * the sole owner). The landing date is computed by the pure `resolveStep` authority (snapshot-only,
 * bounded, Latest-normalised). `canPrev`/`canNext` drive the buttons' disabled state at the ends.
 */
export function useAsOfStep(): {
  stepPrev: () => void;
  stepNext: () => void;
  canPrev: boolean;
  canNext: boolean;
} {
  const { asOf, setAsOf, dates } = useAsOf();
  const stepPrev = useCallback(() => {
    const { changed, next } = resolveStep(dates, asOf, -1);
    if (changed) setAsOf(next);
  }, [dates, asOf, setAsOf]);
  const stepNext = useCallback(() => {
    const { changed, next } = resolveStep(dates, asOf, 1);
    if (changed) setAsOf(next);
  }, [dates, asOf, setAsOf]);
  return {
    stepPrev,
    stepNext,
    canPrev: canStepPrev(dates, asOf),
    canNext: canStepNext(dates, asOf),
  };
}

/**
 * J-50 — the ONE canonical builder of an in-app link's `href` that embeds the global as-of date.
 *
 * This is the single implementation every navigational link uses: it reads the one global as-of
 * state (the same `ASOF_PARAM` this provider owns) and serializes it into the link's `href` while
 * historical, leaving the `href` date-free at latest. No component builds the `?asof` string itself —
 * the URL serialization of the single date state has exactly one author here, mirroring how
 * `AsOfUrlSync` is the sole writer of `?asof` onto the *current* page. So middle-click / new-tab /
 * copied-link navigation lands on the same dated view WITHOUT depending on post-navigation re-stamping.
 *
 * The returned `asofHref(path)`:
 *  - takes a same-origin app path that MAY already carry its own query string (e.g.
 *    `/stocks?pattern=vcp__only`) and/or a hash, and merges `asof` into it without clobbering them;
 *  - while historical, sets `asof=<D>`; at latest (or before the run list resolves), it emits the
 *    clean path with NO `asof` param (and strips any `asof` the caller mistakenly included);
 *  - never fabricates a date and never reads/holds a second date state — it only re-formats the one
 *    global `asOf` value into the link.
 */
export function useAsOfHref(): (path: string) => string {
  const { asOf, isHistorical } = useAsOf();
  return useCallback(
    (path: string) => {
      // Split off any hash so it is preserved after the query string we (re)write.
      const hashIndex = path.indexOf("#");
      const hash = hashIndex >= 0 ? path.slice(hashIndex) : "";
      const beforeHash = hashIndex >= 0 ? path.slice(0, hashIndex) : path;
      const queryIndex = beforeHash.indexOf("?");
      const basePath = queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash;
      const params = new URLSearchParams(queryIndex >= 0 ? beforeHash.slice(queryIndex + 1) : "");
      // The single state decides the param: historical → asof=D; latest/loading → no asof at all.
      if (isHistorical && asOf) params.set(ASOF_PARAM, asOf);
      else params.delete(ASOF_PARAM);
      const query = params.toString();
      return `${basePath}${query ? `?${query}` : ""}${hash}`;
    },
    [asOf, isHistorical],
  );
}
