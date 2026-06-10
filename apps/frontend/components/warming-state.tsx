"use client";

import { Loader2 } from "lucide-react";

import { useReadiness } from "@/components/readiness-provider";
import { Card } from "@/components/ui/card";

/**
 * The transient "warming up — historical evidence still loading (n/m)" state for the analytics pages
 * (iter-28, J-40). While the background historical warm-up is still loading (readiness = `initializing`),
 * `/backtest` and `/research` render THIS card instead of an error, an empty result, or a partial result
 * presented as complete. It reads the SAME single readiness value (via `useReadiness`) the badge reads —
 * it adds NO date state (J-18 preserved) and computes no readiness itself. Once warm-up finishes the
 * pages auto-populate (the page effect re-reads the now-complete evidence).
 *
 * `shouldWarm()` is the single predicate the pages gate on, so the rule lives in one place.
 */
export function shouldShowWarming(state: ReturnType<typeof useReadiness>["state"]): boolean {
  return state === "initializing";
}

export function WarmingState({ what }: { what: string }) {
  const { warmup } = useReadiness();
  const progress = warmup ? `${warmup.done}/${warmup.total}` : "";
  return (
    <Card
      className="flex items-start gap-3 border-warn bg-surface p-5 text-sm"
      data-testid="warming-state"
    >
      <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-warn" aria-hidden />
      <div className="space-y-1">
        <p className="font-medium text-warn">
          Warming up — historical evidence still loading{" "}
          {progress ? <span className="num">({progress})</span> : null}
        </p>
        <p className="text-text-muted">
          {what} is computed from the background walk-forward warm-up, which is still producing the
          historical snapshots and forward returns. This page will populate automatically when it finishes
          — no result is shown rather than a partial or fabricated one.
        </p>
      </div>
    </Card>
  );
}
