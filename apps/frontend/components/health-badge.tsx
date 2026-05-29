"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { fetchHealth, type HealthStatus } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthStatus }
  | { kind: "error" };

/** Live backend-connectivity badge: the visible proof the frontend talks to the offline
 *  seed spine. Shows loading -> connected (provider + latest seed date + symbol count) or an
 *  explicit "Backend unavailable" — never a fabricated "ok". Re-checks every 30s. */
export function HealthBadge() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await fetchHealth();
        if (active) setState({ kind: "ok", data });
      } catch {
        if (active) setState({ kind: "error" });
      }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <Badge variant="default">
        <span className="h-2 w-2 animate-pulse rounded-full bg-text-faint" aria-hidden />
        Checking backend…
      </Badge>
    );
  }

  if (state.kind === "error") {
    return (
      <Badge variant="danger">
        <span className="h-2 w-2 rounded-full bg-neg" aria-hidden />
        Backend unavailable
      </Badge>
    );
  }

  const { data } = state;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="ok">
        <span className="h-2 w-2 rounded-full bg-pos" aria-hidden />
        Backend OK
      </Badge>
      <Badge variant="accent">provider: {data.provider}</Badge>
      <Badge variant="default" className="num">
        seed {data.seed_latest_date ?? "—"}
      </Badge>
      <Badge variant="default" className="num">
        {data.symbol_count} symbols
      </Badge>
    </div>
  );
}
