"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, SearchX } from "lucide-react";

import { ComponentBreakdown } from "@/components/component-breakdown";
import { PageHeading } from "@/components/page-heading";
import { ScoreBadge } from "@/components/score-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchStock, type ScoreBlock, type StockDetailResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: StockDetailResponse }
  | { kind: "notfound" }
  | { kind: "error" };

function setupVariant(status: string): "ok" | "warn" | "danger" | "accent" | "default" {
  switch (status) {
    case "Actionable":
      return "ok";
    case "Breakout-watch":
    case "Pullback-watch":
      return "accent";
    case "Extended":
    case "Risk-off-watchlist":
      return "warn";
    case "Avoid":
      return "danger";
    default:
      return "default";
  }
}

export default function StockDetailPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = (params?.ticker ?? "").toUpperCase();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!ticker) return;
    const controller = new AbortController();
    fetchStock(ticker, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch((err: Error) => {
        if (controller.signal.aborted) return;
        setState({ kind: err.message.includes("404") ? "notfound" : "error" });
      });
    return () => controller.abort();
  }, [ticker]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <PageHeading
          title={ticker}
          subtitle="Stock detail — the three explainable scores (identical to the leaderboard; single source of truth)"
        />
        <Link
          href="/stocks"
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text focus-visible:text-text focus-visible:outline-none"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Back to leaderboard
        </Link>
      </div>

      {state.kind === "loading" ? <DetailSkeleton /> : null}

      {state.kind === "notfound" ? (
        <Card className="flex items-center gap-3 border-warn bg-surface p-5 text-sm text-warn">
          <SearchX className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Unknown ticker</p>
            <p className="text-text-muted">
              “{ticker}” is not in the scanned universe. Open a stock from the{" "}
              <Link href="/stocks" className="text-accent hover:underline">
                leaderboard
              </Link>
              .
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "error" ? (
        <Card className="flex items-center gap-3 border-neg bg-surface p-5 text-sm text-neg">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
          <div>
            <p className="font-medium">Backend unavailable</p>
            <p className="text-text-muted">
              This stock’s scores could not load from the API. Nothing is fabricated — confirm the
              backend is running and reload.
            </p>
          </div>
        </Card>
      ) : null}

      {state.kind === "ok" ? <StockDetailBody data={state.data} /> : null}
    </div>
  );
}

function StockDetailBody({ data }: { data: StockDetailResponse }) {
  const { row } = data;
  return (
    <div className="space-y-4">
      {/* setup + reason header */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-5">
          <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
          <span className="text-xs text-text-muted">{row.sector}</span>
          <Badge variant="default" className="num">
            as of {data.asof_date}
          </Badge>
          <p className="w-full text-sm text-text-muted">{row.setup.reason}</p>
        </CardContent>
      </Card>

      {/* three independent scores */}
      <div className="grid gap-4 lg:grid-cols-3">
        <ScoreCard title="Leadership" caption="How strong the stock is (higher = stronger)" block={row.leadership} />
        <ScoreCard
          title="Entry Quality"
          caption="Is the entry buyable or extended (higher = better entry)"
          block={row.entry_quality}
        />
        <ScoreCard
          title="Risk"
          caption="Danger factors (higher = MORE dangerous)"
          block={row.risk}
          invert
        />
      </div>

      <p className="text-xs text-text-faint">
        A price + moving-average chart, theme-membership chips, and a concrete invalidation level
        arrive in the next iteration. iter-3’s detail page exists to prove the scores are identical
        to the leaderboard (single source of truth).
      </p>
    </div>
  );
}

function ScoreCard({
  title,
  caption,
  block,
  invert = false,
}: {
  title: string;
  caption: string;
  block: ScoreBlock;
  invert?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>{title}</CardTitle>
        <ScoreBadge bucket={block.bucket} score={block.score} invert={invert} />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline gap-2">
          <span className="num text-3xl font-semibold text-text">{block.score.toFixed(2)}</span>
          <span className="text-xs text-text-muted">/ 100</span>
        </div>
        <p className="text-xs text-text-faint">{caption}</p>
        <ComponentBreakdown components={block.components} />
      </CardContent>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <Card className="h-20 animate-pulse bg-surface-2" />
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="h-72 animate-pulse bg-surface-2" />
        ))}
      </div>
    </div>
  );
}
