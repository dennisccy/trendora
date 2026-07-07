"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, SearchX } from "lucide-react";

import { useAsOf, useAsOfHref } from "@/components/asof-provider";
import { ComponentBreakdown } from "@/components/component-breakdown";
import { EvidenceStatusBadge } from "@/components/evidence-status-badge";
import { fmtMdd, fmtPct, mddClass, returnClass } from "@/components/forward-return";
import { PageHeading } from "@/components/page-heading";
import { PriceChart } from "@/components/price-chart";
import { ScoreBadge } from "@/components/score-badge";
import { ScoreProofPanel } from "@/components/score-proof-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatIsoDate } from "@/lib/dates";
import { SCORE_SIGNALS } from "@/lib/evidence";
import { sectorLabel } from "@/lib/sector-label";
import { cn } from "@/lib/utils";
import {
  fetchEvidence,
  fetchRegimeHistory,
  fetchStock,
  fetchStockBars,
  type BarsResponse,
  type ProvenSignal,
  type RegimePoint,
  type ScoreBlock,
  type StockDetailResponse,
  type StockRow,
  type Vcp,
} from "@/lib/api";
import { usePersistedToggle } from "@/lib/use-persisted-toggle";

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

/** A detected price pattern's read-only flag shape — VCP and the iter-9 additions share this contract. */
type PatternFlag = {
  flagged: boolean;
  reason: string;
  pivot: number | null;
  invalidation: { level: number | null; note: string };
};

/** The iter-9 detected patterns that ride the detail page alongside VCP. Adding one is a single entry
 *  here — the header badge and the pattern card both read this list (config-driven UI vocabulary). */
const NEW_PATTERNS: { key: string; name: string; badge: string; get: (row: StockRow) => PatternFlag }[] = [
  { key: "pullback_to_rising_dma", name: "Pullback to a rising DMA", badge: "Pullback", get: (r) => r.pullback_to_rising_dma },
  { key: "flat_base_breakout", name: "Flat-base breakout", badge: "Flat base", get: (r) => r.flat_base_breakout },
];

/** A pattern badge tooltip: the server-built reason + pivot + invalidation note, rendered verbatim. */
function patternTitle(flag: PatternFlag): string {
  return [flag.reason, flag.pivot != null ? `Pivot $${flag.pivot.toFixed(2)}.` : null, flag.invalidation.note]
    .filter(Boolean)
    .join(" ");
}

export default function StockDetailPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = (params?.ticker ?? "").toUpperCase();
  const { asOf } = useAsOf();
  // J-50: in-app links on this page carry the global as-of date while historical (clean at latest) via
  // the one shared helper, so middle-click / new-tab / copied-link from the detail view stays dated.
  const asofHref = useAsOfHref();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!ticker) return;
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchStock(ticker, asOf ?? undefined, controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch((err: Error) => {
        if (controller.signal.aborted) return;
        setState({ kind: err.message.includes("404") ? "notfound" : "error" });
      });
    return () => controller.abort();
  }, [ticker, asOf]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <PageHeading
          title={ticker}
          subtitle="Stock detail — the three explainable scores (identical to the leaderboard; single source of truth)"
        />
        <Link
          href={asofHref("/stocks")}
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
              <Link href={asofHref("/stocks")} className="text-accent hover:underline">
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
  // goal-mcp-loop iter-1 — the served proven-signal map (from /api/evidence). Default `{}` is the
  // FAIL-SAFE: until/unless evidence loads, every score badge reads "Not yet proven". Fetched ONCE,
  // NON-blocking: a failure leaves it `{}` and never breaks the score cards. The UI never computes
  // proven-ness — it re-displays this served map (empty ledger ⇒ every badge "Not yet proven").
  const [provenSignals, setProvenSignals] = useState<Record<string, ProvenSignal>>({});
  useEffect(() => {
    const controller = new AbortController();
    fetchEvidence(controller.signal)
      .then((evidence) => setProvenSignals(evidence.proven_signals ?? {}))
      .catch(() => {
        if (!controller.signal.aborted) setProvenSignals({});
      });
    return () => controller.abort();
  }, []);
  return (
    <div className="space-y-4">
      {/* setup + reason header — each detected pattern badge rides ALONGSIDE the setup status, never replacing it */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-5">
          <Badge variant={setupVariant(row.setup.status)}>{row.setup.status}</Badge>
          {row.vcp.flagged ? <VcpBadge vcp={row.vcp} /> : null}
          {NEW_PATTERNS.filter((p) => p.get(row).flagged).map((p) => (
            <PatternBadge key={p.key} label={p.badge} flag={p.get(row)} />
          ))}
          <span className="text-xs text-text-muted">{sectorLabel(row.sector)}</span>
          <Badge variant="default" className="num">
            as of {formatIsoDate(data.asof_date)}
          </Badge>
          <p className="w-full text-sm text-text-muted">{row.setup.reason}</p>
        </CardContent>
      </Card>

      {/* theme membership + concrete invalidation level (server-computed, rendered verbatim) */}
      <ThemeAndInvalidationCard row={row} />

      {/* detected patterns — each a separate pattern with its own pivot + invalidation level. VCP always
          shows (incl. a not-detected state); the iter-9 patterns show a card only when flagged. */}
      <VcpCard vcp={row.vcp} />
      {NEW_PATTERNS.filter((p) => p.get(row).flagged).map((p) => (
        <PatternCard key={p.key} name={p.name} badge={p.badge} flag={p.get(row)} />
      ))}

      {/* J-75 — the five realized forward returns (1/5/10/20/60-day) for the as-of date, read VERBATIM
          from the stored forward_returns table — the SAME values the leaderboard + Backtest show (single
          source; J-06/J-21). NA where no stored row (at/near latest all five NA — never fabricated). */}
      <ForwardReturnPanel row={row} asofDate={data.asof_date} />

      {/* price + moving-average candle chart with volume (server MA series — never recomputed) */}
      <StockChartPanel ticker={row.ticker} />

      {/* three independent scores — each now carries an inline evidence-status badge (purely additive;
          the score value is unchanged). Against the empty ledger every badge reads "Not yet proven". */}
      <div className="grid gap-4 lg:grid-cols-3">
        <ScoreCard
          title="Leadership"
          caption="How strong the stock is (higher = stronger)"
          block={row.leadership}
          signal={SCORE_SIGNALS.leadership}
          provenSignals={provenSignals}
        />
        <ScoreCard
          title="Entry Quality"
          caption="Is the entry buyable or extended (higher = better entry)"
          block={row.entry_quality}
          signal={SCORE_SIGNALS.entry_quality}
          provenSignals={provenSignals}
        />
        <ScoreCard
          title="Risk"
          caption="Danger factors (higher = MORE dangerous)"
          block={row.risk}
          signal={SCORE_SIGNALS.risk}
          provenSignals={provenSignals}
          invert
        />
      </div>
    </div>
  );
}

function ThemeAndInvalidationCard({ row }: { row: StockRow }) {
  const asofHref = useAsOfHref();
  const naInvalidation = row.invalidation.level == null;
  return (
    <Card>
      <CardContent className="grid gap-4 p-5 md:grid-cols-2">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-text-faint">Themes</p>
          {row.themes.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {row.themes.map((theme) => (
                <Link
                  key={theme.slug}
                  href={asofHref("/themes")}
                  className="rounded-md focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
                >
                  <Badge variant="accent" className="hover:bg-surface active:bg-bg">
                    {theme.name}
                  </Badge>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted">Not a member of any tracked theme.</p>
          )}
        </div>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-text-faint">Invalidation</p>
          <p className={cn("text-sm", naInvalidation ? "text-warn" : "text-text-muted")}>
            {row.invalidation.note}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/** The VCP badge that rides ALONGSIDE the setup status (teal accent). Its tooltip carries the
 *  server-built reason + pivot + invalidation note (rendered verbatim — never assembled here). */
function VcpBadge({ vcp }: { vcp: Vcp }) {
  const title = [
    vcp.reason,
    vcp.pivot != null ? `Pivot $${vcp.pivot.toFixed(2)}.` : null,
    vcp.invalidation.note,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <Badge variant="accent" title={title} className="cursor-help">
      VCP
    </Badge>
  );
}

/** The dedicated VCP pattern card: a SEPARATE detected pattern with its OWN pivot + invalidation
 *  level (distinct from the setup invalidation above). When not flagged it states so explicitly —
 *  no fabricated pivot. The same stored value the leaderboard serves (single source → J-06). */
function VcpCard({ vcp }: { vcp: Vcp }) {
  if (!vcp.flagged) {
    return (
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-5">
          <p className="text-xs uppercase tracking-wide text-text-faint">VCP pattern</p>
          <p className="text-sm text-text-muted">No VCP pattern detected.</p>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>VCP — Volatility Contraction Pattern</CardTitle>
        <Badge variant="accent">VCP</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-text-muted">{vcp.reason}</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-text-faint">Pivot (breakout level)</p>
            <p className="num text-lg font-semibold text-text">
              {vcp.pivot != null ? `$${vcp.pivot.toFixed(2)}` : "—"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-text-faint">Invalidation</p>
            <p className="text-sm text-warn">{vcp.invalidation.note}</p>
          </div>
        </div>
        {vcp.contractions && vcp.contractions.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs uppercase tracking-wide text-text-faint">Contractions</span>
            {vcp.contractions.map((c, i) => (
              <Badge key={i} variant="default" className="num">
                {c.toFixed(0)}%
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

/** A detected-pattern badge (iter-9) that rides ALONGSIDE the setup status (teal accent). Its tooltip
 *  carries the server-built reason + pivot + invalidation note (rendered verbatim — never assembled). */
function PatternBadge({ label, flag }: { label: string; flag: PatternFlag }) {
  return (
    <Badge variant="accent" title={patternTitle(flag)} className="cursor-help">
      {label}
    </Badge>
  );
}

/** A dedicated detected-pattern card (iter-9): a SEPARATE pattern with its OWN pivot + invalidation
 *  level. Rendered only when flagged. The same stored value the leaderboard serves (single source → J-06);
 *  reason/pivot/invalidation are server-built and rendered verbatim — never recomputed client-side. */
function PatternCard({ name, badge, flag }: { name: string; badge: string; flag: PatternFlag }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>{name}</CardTitle>
        <Badge variant="accent">{badge}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-text-muted">{flag.reason}</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-text-faint">Pivot (breakout level)</p>
            <p className="num text-lg font-semibold text-text">
              {flag.pivot != null ? `$${flag.pivot.toFixed(2)}` : "—"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-text-faint">Invalidation</p>
            <p className="text-sm text-warn">{flag.invalidation.note}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

type ChartState =
  | { kind: "loading" }
  | { kind: "ok"; data: BarsResponse }
  | { kind: "empty" }
  | { kind: "error" };

function StockChartPanel({ ticker }: { ticker: string }) {
  const { asOf } = useAsOf();
  const [state, setState] = useState<ChartState>({ kind: "loading" });
  // J-45: regime bands behind price. Stored regime history (date <= as-of), same endpoint + lib/regime
  // mapping as the dashboard card, fetched at the SAME as-of so the same date shows the same band color.
  const [regimePoints, setRegimePoints] = useState<RegimePoint[]>([]);
  // Regime band toggle — a client display preference, default ON, persisted across reloads (J-45).
  const [regimeOn, setRegimeOn] = usePersistedToggle("trendora.detail.regimeBands", true);
  // iter-18 (J-10): the chart RANGE — bounded recent window by default (the deep basis never ships every
  // bar by default), with an explicit full-real-history opt-in. A display preference, persisted like the
  // regime toggle; the selection is sent as the SAME endpoint's `range` param (no client-side slicing).
  const [fullHistory, setFullHistory] = usePersistedToggle("trendora.detail.chartFullHistory", false);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    // J-20: opt into the DISPLAY-ONLY full path through the latest seed date. At a historical as-of D
    // the chart shows the post-D region (labelled forward); the scores/setup/VCP below still read
    // `fetchStock` (the <= D snapshot) — the forward bars never reach the scoring path.
    // iter-18: the selected range rides the same request (server-side presentation bounding).
    fetchStockBars(ticker, asOf ?? undefined, controller.signal, "latest", fullHistory ? "full" : undefined)
      .then((data) => setState(data.bars.length > 0 ? { kind: "ok", data } : { kind: "empty" }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [ticker, asOf, fullHistory]);

  // Regime history loads independently (same as-of); a failure just means no bands (never blocks the chart).
  useEffect(() => {
    const controller = new AbortController();
    setRegimePoints([]);
    fetchRegimeHistory(asOf ?? undefined, controller.signal)
      .then((res) => setRegimePoints(res.points))
      .catch(() => {
        /* bands are optional — a regime-history failure leaves the price chart fully functional */
      });
    return () => controller.abort();
  }, [asOf]);

  const hasForward = state.kind === "ok" && state.data.bars.some((bar) => bar.is_forward);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Price &amp; moving averages</CardTitle>
        <div className="flex items-center gap-3">
          <ChartRangeControl full={fullHistory} onChange={setFullHistory} />
          <RegimeToggle on={regimeOn} onChange={setRegimeOn} />
          {state.kind === "ok" ? (
            <span className="num text-xs text-text-faint" data-testid="chart-window-caption">
              {state.data.bars.length} bars · as of {formatIsoDate(state.data.asof_date)} · history since{" "}
              {formatIsoDate(state.data.first_available_date)}
              {state.data.downsampled ? " · older bars weekly-sampled" : ""}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {state.kind === "loading" ? (
          <div className="h-80 w-full animate-pulse rounded bg-surface-2" />
        ) : null}
        {state.kind === "ok" ? (
          <div className="space-y-3">
            {hasForward ? (
              <p className="text-xs text-text-faint">
                Full path through {state.data.latest_date ? formatIsoDate(state.data.latest_date) : "the latest seed date"}. Bars after the
                as-of date {formatIsoDate(state.data.asof_date)} are{" "}
                <span className="text-warn">display-only</span> — they don’t affect the scores, setup,
                or VCP flag below (those read the as-of snapshot, bars ≤ {formatIsoDate(state.data.asof_date)}).
              </p>
            ) : null}
            <PriceChart
              bars={state.data.bars}
              ma={state.data.ma}
              asofDate={state.data.asof_date}
              regimePoints={regimePoints}
              regimeEnabled={regimeOn}
            />
          </div>
        ) : null}
        {state.kind === "empty" ? (
          <div className="flex h-80 items-center justify-center text-sm text-text-muted">
            No price history is available for {ticker}.
          </div>
        ) : null}
        {state.kind === "error" ? (
          <div className="flex h-80 items-center gap-3 rounded border border-warn bg-surface p-5 text-sm text-warn">
            <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden />
            <div>
              <p className="font-medium">Chart unavailable</p>
              <p className="text-text-muted">
                The price series could not load from the API. Nothing is fabricated — the scores
                above are unaffected; confirm the backend is running and reload.
              </p>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

/** J-45 Regime band toggle — a small, accessible switch in the chart controls (default ON, persisted
 *  client-side). Shows/hides the soft regime background bands; it changes no served value. */
/** iter-18 (J-10) — the chart range control: a two-option segmented toggle between the BOUNDED recent
 *  window (the server default — the deep basis never ships every bar by default) and the explicit
 *  full-real-history opt-in (`range=full`, weekly-sampled beyond the config span server-side). Pure
 *  presentation state — the selection changes only the SAME endpoint's `range` param; the page never
 *  slices or recomputes a series client-side. */
function ChartRangeControl({ full, onChange }: { full: boolean; onChange: (next: boolean) => void }) {
  const options = [
    { key: "recent", label: "Recent", full: false, title: "Bounded recent window (server default)" },
    { key: "full", label: "Full history", full: true, title: "Entire real history — deep bars weekly-sampled" },
  ];
  return (
    <div
      className="flex items-center overflow-hidden rounded border border-border"
      role="group"
      aria-label="Chart range"
      data-testid="chart-range-control"
    >
      {options.map((opt) => (
        <button
          key={opt.key}
          type="button"
          title={opt.title}
          aria-pressed={full === opt.full}
          onClick={() => onChange(opt.full)}
          data-testid={`chart-range-${opt.key}`}
          className={cn(
            "px-2.5 py-1 text-xs transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
            full === opt.full
              ? "bg-surface-2 text-text"
              : "bg-surface text-text-muted hover:text-text active:bg-surface-2",
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function RegimeToggle({ on, onChange }: { on: boolean; onChange: (next: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={cn(
        "group flex items-center gap-2 rounded border px-2.5 py-1 text-xs transition-colors",
        "focus:outline-none focus-visible:ring-1 focus-visible:ring-accent",
        on
          ? "border-border-strong bg-surface-2 text-text"
          : "border-border bg-surface text-text-muted hover:text-text",
      )}
    >
      <span
        className={cn(
          "inline-block h-2 w-2 rounded-sm transition-opacity",
          on ? "opacity-100" : "opacity-40",
        )}
        style={{ backgroundColor: "var(--warn)" }}
        aria-hidden
      />
      Regime {on ? "on" : "off"}
    </button>
  );
}

/** J-75 — the per-stock realized forward-return panel for the resolved as-of date: one cell per config
 *  horizon (1/5/10/20/60-day), each the stored `realized_return` read VERBATIM (NA where no stored row —
 *  at/near the latest date all five are NA, never fabricated). These are the SAME stored values the
 *  leaderboard row and Backtest show for the same ticker/date/horizon (single source of truth — J-06 /
 *  J-21); the panel re-formats only and recomputes nothing. Measured from the close on the as-of date to
 *  the close of the h-th post-as-of bar (no-lookahead intrinsic to the stored rows). */
function ForwardReturnPanel({ row, asofDate }: { row: StockRow; asofDate: string }) {
  return (
    <Card data-testid="forward-return-panel">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Realized forward returns</CardTitle>
        <Badge variant="default" className="num">
          from {formatIsoDate(asofDate)}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-text-faint">
          The realized return measured from the close on {formatIsoDate(asofDate)} to the close{" "}
          {row.forward_returns.map((fr) => fr.horizon).join(" / ")} trading days later — read verbatim from
          the stored walk-forward returns (the SAME values the leaderboard and Backtest show). Each return is
          paired with its max drawdown (J-86 — the worst peak-to-trough decline over that window, &le; 0). NA
          where not enough post-date bars exist yet (never fabricated).
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {row.forward_returns.map((fr) => (
            <div
              key={fr.horizon}
              className="rounded-md border border-border bg-surface-2 p-3"
              data-testid={`detail-fwd-${fr.horizon}`}
            >
              <p className="text-xs uppercase tracking-wide text-text-faint">{fr.horizon}-day</p>
              {fr.return === null || fr.return === undefined ? (
                <p className="num text-lg font-semibold text-text-muted" title="No realized forward return at this horizon yet (NA)">
                  NA
                </p>
              ) : (
                <p className={cn("num text-lg font-semibold", returnClass(fr.return))}>
                  {fmtPct(fr.return)}
                </p>
              )}
              {/* J-86 — the paired max-drawdown beside the realized return (read verbatim; <= 0 or NA). */}
              <p className="mt-1 text-[10px] uppercase tracking-wide text-text-faint">Max drawdown</p>
              <p
                className={cn("num text-sm font-semibold", mddClass(fr.max_drawdown))}
                data-testid={`detail-mdd-${fr.horizon}`}
                title={
                  fr.max_drawdown === null || fr.max_drawdown === undefined
                    ? "No realized max drawdown at this horizon yet (NA)"
                    : undefined
                }
              >
                {fmtMdd(fr.max_drawdown)}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ScoreCard({
  title,
  caption,
  block,
  signal,
  provenSignals,
  invert = false,
}: {
  title: string;
  caption: string;
  block: ScoreBlock;
  /** goal-mcp-loop iter-1 — the evidence-ledger signal key this score maps to. */
  signal: string;
  /** goal-mcp-loop iter-1 — the served proven-signal map; drives the inline evidence-status badge. */
  provenSignals: Record<string, ProvenSignal>;
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
        {/* goal-mcp-loop iter-1 — the inline evidence status for this score (purely additive; the score
            above is unchanged). A PASS-backed signal reads "Proven"; everything else "Not yet proven". */}
        <EvidenceStatusBadge signal={signal} provenSignals={provenSignals} />
        {/* goal-mcp-loop iter-2 (J-02) — when this score is PROVEN, a collapsed-by-default "Why proven?"
            disclosure expands in place to audit the out-of-sample test, the SPY control comparison, and the
            certified-claim id/date (read verbatim from the served map; renders nothing when not proven). */}
        <ScoreProofPanel signal={signal} provenSignals={provenSignals} />
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
