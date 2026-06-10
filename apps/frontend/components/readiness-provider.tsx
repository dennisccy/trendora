"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

import { fetchHealth, type ReadinessState, type WarmupProgress } from "@/lib/api";

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
 */
export interface ReadinessContextValue {
  /** The honest backend readiness state, or null before the first poll resolves. */
  state: ReadinessState | null;
  /** The background warm-up progress (history n/m), or null before the first poll. */
  warmup: WarmupProgress | null;
  /** True until the first poll has resolved (so callers can show a neutral "checking" state). */
  loading: boolean;
}

const ReadinessContext = createContext<ReadinessContextValue | null>(null);

// Fallback cadences (ms) used ONLY before the first payload arrives (so the very first poll can be
// scheduled); once a payload is read the config-derived cadences from the backend take over. These are
// bootstrap defaults for the initial tick, not scoring/behaviour tunables.
const BOOTSTRAP_ACTIVE_MS = 2_000;

export function ReadinessProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ReadinessState | null>(null);
  const [warmup, setWarmup] = useState<WarmupProgress | null>(null);
  const [loading, setLoading] = useState(true);
  // the config-derived cadences (seconds) from the latest payload; refs so the polling loop reads the
  // freshest value without re-subscribing.
  const activeMs = useRef(BOOTSTRAP_ACTIVE_MS);
  const idleMs = useRef(BOOTSTRAP_ACTIVE_MS);

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
        // adopt the config-derived poll cadences (seconds → ms); never a client-side literal.
        activeMs.current = Math.max(250, Math.round(data.poll_interval_seconds * 1000));
        idleMs.current = Math.max(activeMs.current, Math.round(data.poll_idle_interval_seconds * 1000));
        // poll fast while still warming; back off to the idle cadence once ready.
        nextDelay = data.readiness === "ready" ? idleMs.current : activeMs.current;
      } catch {
        if (!active) return;
        setState("unavailable"); // honest — never a fabricated ok
        setWarmup(null);
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

  const value = useMemo<ReadinessContextValue>(
    () => ({ state, warmup, loading }),
    [state, warmup, loading],
  );

  return <ReadinessContext.Provider value={value}>{children}</ReadinessContext.Provider>;
}

/** Read the global readiness state. Must be used within `<ReadinessProvider>` (mounted in the app shell). */
export function useReadiness(): ReadinessContextValue {
  const ctx = useContext(ReadinessContext);
  if (!ctx) throw new Error("useReadiness must be used within <ReadinessProvider>");
  return ctx;
}
