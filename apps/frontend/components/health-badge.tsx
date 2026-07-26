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
 *  Initializing…, Snapshot pending (ops-hardening iter-4, B3 fix), or Unavailable. It reads the SINGLE
 *  shared readiness value from `useReadiness` (one client-side readiness read; the frontend never
 *  computes readiness itself). The provider/seed/symbol/recovery-detail badges fetch the rest of the
 *  health payload for context, re-fetching whenever the shared `state` transitions (see the effect below)
 *  so the `awaiting_snapshot` recovery-pointer text stays in sync with the SAME transition the pill
 *  re-renders for, without a second polling loop. Re-checks of `state`/`warmup` themselves happen via the
 *  readiness provider's own config-derived poll. */
export function HealthBadge() {
  const { state, warmup, backgroundCompute, loading } = useReadiness();
  const [detail, setDetail] = useState<Detail>({ kind: "loading" });

  // The context detail (provider / seed date / symbol count / the `awaiting_snapshot` recovery-pointer
  // string). Re-fetched whenever the shared readiness `state` transitions -- state changes are
  // infrequent, so this stays cheap, and it keeps the recovery-pointer text synced to the exact moment
  // the pill below flips to `awaiting_snapshot` (rather than only refreshing once on mount, which could
  // show the new pill with a stale/missing detail until some unrelated future reload). If it fails, the
  // readiness pill still renders honestly — it reads `state`/`warmup` from `useReadiness()` directly,
  // never from this fetch.
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
  }, [state]);

  // --- the readiness pill (the load-bearing four-state badge) ---
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
  } else if (state === "awaiting_snapshot") {
    // ops-hardening iter-4 (B3 fix): a servable last run exists, but new data has landed for the
    // benchmark symbol that defines the trading calendar and no snapshot covers it yet -- a calm,
    // honest, non-danger state (never "Backend unavailable"). The dot is static (not animate-pulse):
    // unlike `initializing`'s self-resolving warm-up, this condition persists until an operator runs a
    // backfill/rebuild on Data Manager, so it reads as "needs action," not "in progress automatically."
    const recoveryDetail = detail.kind === "ok" ? detail.data.readiness_detail : null;
    pill = (
      <Badge variant="accent" data-testid="readiness-badge" data-state="awaiting_snapshot">
        <span className="h-2 w-2 rounded-full bg-accent" aria-hidden />
        <span>Snapshot pending{recoveryDetail ? ` — ${recoveryDetail}` : ""}</span>
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

  // ops-hardening iter-24 (J-09): the historical background-compute disclosure -- one additional inline
  // element, present alongside the pill in ANY readiness state whenever a window is in flight, absent
  // entirely when none is (never replaces/hides the pill above). Reads the SAME shared readiness poll
  // (`useReadiness()`) -- no second fetch.
  const activeComputeCount = backgroundCompute?.active.length ?? 0;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {pill}
      {activeComputeCount > 0 ? (
        <Badge variant="accent" className="num gap-1.5" data-testid="background-compute-indicator">
          <span className="h-2 w-2 animate-pulse rounded-full bg-accent" aria-hidden />
          background compute running ({activeComputeCount})
        </Badge>
      ) : null}
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
