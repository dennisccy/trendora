"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { useReadiness } from "@/components/readiness-provider";
import { fetchHealth, type HealthStatus } from "@/lib/api";

type Detail =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthStatus }
  | { kind: "error" };

/** Live backend readiness badge (iter-28, J-40): the visible truth about backend state — Ready,
 *  Initializing… (with live "history n/m" warm-up progress), or Unavailable. It reads the SINGLE shared
 *  readiness value from `useReadiness` (one client-side readiness read; the frontend never computes
 *  readiness itself). The provider/seed/symbol detail badges fetch the rest of the health payload once
 *  for context. Re-checks happen via the readiness provider's config-derived poll. */
export function HealthBadge() {
  const { state, warmup, loading } = useReadiness();
  const [detail, setDetail] = useState<Detail>({ kind: "loading" });

  // The static-ish context detail (provider / seed date / symbol count). Fetched once; it does not
  // need the fast readiness cadence. If it fails, the readiness badge still renders honestly.
  useEffect(() => {
    let active = true;
    fetchHealth()
      .then((data) => {
        if (active) setDetail({ kind: "ok", data });
      })
      .catch(() => {
        if (active) setDetail({ kind: "error" });
      });
    return () => {
      active = false;
    };
  }, []);

  // --- the readiness pill (the load-bearing three-state badge) ---
  let pill;
  if (loading || state === null) {
    pill = (
      <Badge variant="default" data-testid="readiness-badge" data-state="loading">
        <span className="h-2 w-2 animate-pulse rounded-full bg-text-faint" aria-hidden />
        Checking backend…
      </Badge>
    );
  } else if (state === "ready") {
    pill = (
      <Badge variant="ok" data-testid="readiness-badge" data-state="ready">
        <span className="h-2 w-2 rounded-full bg-pos" aria-hidden />
        Ready
      </Badge>
    );
  } else if (state === "initializing") {
    const progress = warmup ? `${warmup.done}/${warmup.total}` : "";
    pill = (
      <Badge variant="warn" data-testid="readiness-badge" data-state="initializing">
        <span className="h-2 w-2 animate-pulse rounded-full bg-warn" aria-hidden />
        <span>
          Initializing…{" "}
          {progress ? <span className="num">history {progress}</span> : null}
        </span>
      </Badge>
    );
  } else {
    // unavailable
    pill = (
      <Badge variant="danger" data-testid="readiness-badge" data-state="unavailable">
        <span className="h-2 w-2 rounded-full bg-neg" aria-hidden />
        Backend unavailable
      </Badge>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {pill}
      {detail.kind === "ok" ? (
        <>
          <Badge variant="accent">provider: {detail.data.provider}</Badge>
          <Badge variant="default" className="num">
            seed {detail.data.seed_latest_date ?? "—"}
          </Badge>
          <Badge variant="default" className="num">
            {detail.data.symbol_count} symbols
          </Badge>
        </>
      ) : null}
    </div>
  );
}
