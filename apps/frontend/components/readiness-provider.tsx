"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

import {
  fetchHealth,
  type BackgroundComputeStatus,
  type PreflightStatus,
  type ReadinessState,
  type WarmupProgress,
} from "@/lib/api";
import { deriveLiveStaleForS } from "@/lib/staleness-tick";

/**
 * Global backend readiness state (iter-28, J-40). A single client context, mounted in the app shell, that
 * polls the SINGLE canonical readiness endpoint (`GET /api/health`) and shares the result — so the top-bar
 * readiness badge AND the Backtest/Research "warming up (n/m)" states all read ONE readiness value (the
 * frontend never computes readiness itself, and there is no second readiness read in the client).
 *
 * The poll cadence is CONFIG-DERIVED (read from the payload's `poll_interval_seconds` /
 * `poll_idle_interval_seconds` — no client-side poll literal): it polls fast while `initializing`/loading
 * (so the flip to Ready shows within ~a poll of warm-up completion) and backs off to the idle cadence once
 * `ready`. On a network/non-200 it surfaces `unavailable` honestly — never a fabricated "ready".
 *
 * iter-33 (J-20): the SAME poll also carries the daily preflight verdict (`preflight`) — the layout-level
 * `PreflightBanner`'s ONLY read path (no second fetch, no per-page recompute).
 *
 * ops-hardening iter-24 (J-09): the SAME poll also carries `background_compute` — the historical
 * background-dispatch disclosure (`HealthBadge`'s conditional indicator + `/data`'s
 * `BackgroundComputePanel` are its ONLY readers; no second fetch, no client-side derivation).
 */
export interface ReadinessContextValue {
  /** The honest backend readiness state, or null before the first poll resolves. */
  state: ReadinessState | null;
  /** The background warm-up progress (history n/m), or null before the first poll. */
  warmup: WarmupProgress | null;
  /** The single GO/DEGRADED/NO-GO preflight verdict, or null before the first poll resolves / on a
   *  failed poll (the backend is unreachable — the banner renders its own honest NO-GO in that case). */
  preflight: PreflightStatus | null;
  /** The historical background-compute dispatch disclosure, or null before the first poll resolves / on
   *  a failed poll (readers render their own honest empty/idle state in that case — never fabricated). */
  backgroundCompute: BackgroundComputeStatus | null;
  /** True until the first poll has resolved (so callers can show a neutral "checking" state). */
  loading: boolean;
  /** goal-ops-hardening iter-61 (J-05) — the config-derived idle cadence (seconds) this SAME poll backs
   *  off to once `ready` (`GET /api/health`'s `poll_idle_interval_seconds`), exposed so a page can run its
   *  OWN ambient/ idle-cadence refresh (e.g. `/data`'s coverage reload) without a second poll literal or a
   *  second fetch. Null before the first poll resolves / on a failed poll (mirrors every sibling field's
   *  honesty convention) — callers must gate their own interval on a non-null value. */
  pollIdleIntervalSeconds: number | null;
  /** ops-hardening iter-77 — the SAME `GET /api/health` payload's `stale_for_s` (seconds since the
   *  served readiness/preflight/background-compute payload was computed; 0 for a fresh synchronous
   *  compute), first rendered by the readiness badge/preflight banner's "as of {N}s ago" annotation.
   *  Null before the first poll resolves / on a failed poll — readers must never render a stale or
   *  fabricated number in that case (mirrors every sibling field's honesty convention).
   *
   *  ops-hardening iter-78 — this value now TICKS between polls: a local 1-second interval re-derives
   *  it (`lib/staleness-tick.ts`'s `deriveLiveStaleForS`, the last poll's own base + elapsed client
   *  seconds since it was received) so it grows smoothly instead of freezing at the last-polled number
   *  for up to the full poll-idle interval. Still the SAME single value, re-formatted only by the
   *  existing `formatStaleAnnotation` — no second poll, no second endpoint, no second formatter. */
  staleForS: number | null;
}

const ReadinessContext = createContext<ReadinessContextValue | null>(null);

// Fallback cadences (ms) used ONLY before the first payload arrives (so the very first poll can be
// scheduled); once a payload is read the config-derived cadences from the backend take over. These are
// bootstrap defaults for the initial tick, not scoring/behaviour tunables.
const BOOTSTRAP_ACTIVE_MS = 2_000;

export function ReadinessProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ReadinessState | null>(null);
  const [warmup, setWarmup] = useState<WarmupProgress | null>(null);
  const [preflight, setPreflight] = useState<PreflightStatus | null>(null);
  const [backgroundCompute, setBackgroundCompute] = useState<BackgroundComputeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [pollIdleIntervalSeconds, setPollIdleIntervalSeconds] = useState<number | null>(null);
  const [staleForS, setStaleForS] = useState<number | null>(null);
  // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
  // freshest value without re-subscribing.
  const activeMs = useRef(BOOTSTRAP_ACTIVE_MS);
  const idleMs = useRef(BOOTSTRAP_ACTIVE_MS);
  // ops-hardening iter-78 — the last poll's own `stale_for_s` base and the client wall-clock time (ms
  // since epoch) it was RECEIVED at, so the 1-second tick below can re-derive a live value between
  // polls without re-fetching or re-subscribing. Refs (not state): the tick interval reads the freshest
  // pair on every fire, and writing them never itself needs to trigger a render (setStaleForS below does
  // that instead).
  const staleBaseRef = useRef<number | null>(null);
  const staleReceivedAtMsRef = useRef<number | null>(null);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const tick = async () => {
      let nextDelay = activeMs.current;
      try {
        const data = await fetchHealth();
        if (!active) return;
        setState(data.readiness);
        setWarmup(data.warmup);
        setPreflight(data.preflight);
        setBackgroundCompute(data.background_compute);
        setPollIdleIntervalSeconds(data.poll_idle_interval_seconds);
        setStaleForS(data.stale_for_s);
        // record this poll's own base + receipt time for the 1-second tick effect below to derive
        // from between now and the next poll landing.
        staleBaseRef.current = data.stale_for_s;
        staleReceivedAtMsRef.current = Date.now();
        // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
        activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
        idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
        // poll fast while still warming; back off to the idle cadence once ready.
        nextDelay = data.readiness === "ready" ? idleMs.current : activeMs.current;
      } catch {
        if (!active) return;
        setState("unavailable"); // honest — never a fabricated ok
        setWarmup(null);
        setPreflight(null); // honest — the banner renders its own NO-GO for a null preflight, never blank
        setBackgroundCompute(null); // honest — readers render their own empty/idle state, never fabricated
        setPollIdleIntervalSeconds(null); // honest — a caller's own idle-refresh loop must not schedule on this
        setStaleForS(null); // honest — never render a stale/fabricated "as of Ns ago" for a failed poll
        staleBaseRef.current = null; // honest — the tick effect must not resume ticking a stale base
        staleReceivedAtMsRef.current = null;
        nextDelay = activeMs.current; // keep retrying at the active cadence until the backend answers
      } finally {
        if (active) {
          setLoading(false);
          timer = setTimeout(tick, nextDelay);
        }
      }
    };

    void tick();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, []);

  // ops-hardening iter-78 (iter-77/d) — a separate, independent 1-second interval that re-derives the
  // LIVE staleness value from the last poll's own base + elapsed client time (`deriveLiveStaleForS`),
  // so the badge/banner annotation grows smoothly between polls instead of freezing at the last-polled
  // number for up to the full poll-idle interval. Deliberately its own effect (not folded into the poll
  // loop above): the poll cadence is config-derived and can be tens of seconds; this tick is a fixed,
  // purely client-side re-render cadence that never itself fetches or schedules a poll.
  useEffect(() => {
    const interval = setInterval(() => {
      setStaleForS(deriveLiveStaleForS(staleBaseRef.current, staleReceivedAtMsRef.current, Date.now()));
    }, 1_000);
    return () => clearInterval(interval);
  }, []);

  const value = useMemo<ReadinessContextValue>(
    () => ({ state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS }),
    [state, warmup, preflight, backgroundCompute, loading, pollIdleIntervalSeconds, staleForS],
  );

  return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
}

/** Read the global readiness state. Must be used within `<ReadinessProvider>` (mounted in the app shell). */
export function useReadiness(): ReadinessContextValue {
  const ctx = useContext(ReadinessContext);
  if (!ctx) throw new Error("useReadiness must be used within <ReadinessProvider>");
  return ctx;
}
