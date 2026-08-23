"use client";

import { useState } from "react";
import { AlertTriangle, Loader2, RotateCcw, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Disclosure } from "@/components/ui/disclosure";
import { basisDisclosureLabel } from "@/lib/basis-disclosure-label";
import { cn } from "@/lib/utils";
import {
  regenerateManifest,
  type CompassCohortRow,
  type CompassComparisonCohortRow,
  type CompassResponse,
} from "@/lib/api";

/** A short, monospace, truncated-with-title hash chip (Visual Requirements: "not decorative" — the
 *  full value is always reachable via the native title tooltip, never only the short form). */
function HashChip({ label, value }: { label: string; value: string | null }) {
  const short = value ? `${value.slice(0, 10)}…` : "—";
  return (
    <span className="flex items-center gap-1.5">
      <span className="text-text-faint">{label}:</span>
      <span
        className="num rounded border border-border bg-surface-2 px-1.5 py-0.5 text-text-muted"
        title={value ?? undefined}
      >
        {short}
      </span>
    </span>
  );
}

function BasisLine({ basis }: { basis: CompassResponse["basis"] }) {
  const { variant, label } = basisDisclosureLabel(basis.status);
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs" data-testid="compass-manifest-basis">
      <Badge variant={variant}>{label}</Badge>
      {basis.detail ? <span className="text-text-faint">{basis.detail}</span> : null}
    </div>
  );
}

/** One audit-table row's field slice — every value is read VERBATIM from the served cohort row, no
 *  client-side derivation. `showDisposition` renders the closed-vocabulary `selection_disposition`
 *  column (comparison-cohort rows only; the shadow cohort carries no disposition — TC-24). */
function CohortTable({
  rows,
  showDisposition,
}: {
  rows: CompassCohortRow[] | CompassComparisonCohortRow[];
  showDisposition: boolean;
}) {
  if (rows.length === 0) {
    return <p className="pt-1 text-xs text-text-faint">No rows.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="text-text-faint">
            <th className="py-1 pr-3">Ticker</th>
            <th className="py-1 pr-3">Leadership</th>
            <th className="py-1 pr-3">Entry</th>
            <th className="py-1 pr-3">Risk</th>
            <th className="py-1 pr-3">Setup</th>
            <th className="py-1 pr-3">Sector</th>
            {showDisposition ? <th className="py-1 pr-3">Disposition</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.ticker} className="border-t border-border" data-testid={`compass-cohort-row-${row.ticker}`}>
              <td className="num py-1 pr-3 font-medium text-text">{row.ticker}</td>
              <td className="num py-1 pr-3 text-text-muted">{row.leadership_score.toFixed(1)}</td>
              <td className="num py-1 pr-3 text-text-muted">{row.entry_quality_score.toFixed(1)}</td>
              <td className="num py-1 pr-3 text-text-muted">{row.risk_score.toFixed(1)}</td>
              <td className="py-1 pr-3 text-text-muted">{row.setup_status}</td>
              <td className="py-1 pr-3 text-text-muted">{row.sector ?? "Unassigned"}</td>
              {showDisposition ? (
                <td className="py-1 pr-3 text-text-muted">
                  {(row as CompassComparisonCohortRow).selection_disposition.replace(/_/g, " ")}
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** goal-market-compass iter-3 (J-05/J-06): the manifest strip — the LAST of the compass cards. Reads
 *  ONLY the extended `GET /api/compass` payload; renders no threshold, no word map, no derived count —
 *  every value is served. AG-13: `generation.preflight_verdict` is DELIBERATELY never rendered here
 *  (readiness/preflight vocabulary must never appear on this surface, TC-31) even though the backend
 *  records it — it stays a provenance-only field, reachable only via the raw API response.
 *
 *  `asOf` (the SAME sole `?asof` owner every other page reads, from `useAsOf()`) gates the confirm-gated
 *  "Regenerate manifest" control: actionable only for a stored HISTORICAL date, never while viewing
 *  "Latest" (`asOf === null`) — regenerating the live-tracking frontier view has no stable target date. */
export function CompassManifestStrip({ compass, asOf }: { compass: CompassResponse | null; asOf: string | null }) {
  const [confirming, setConfirming] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regenerated, setRegenerated] = useState<CompassResponse | null>(null);

  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-manifest-strip-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        Manifest strip is unavailable — backend not reachable, or this session has not been frozen yet.
      </Card>
    );
  }

  // a fresh compass fetch (e.g. the as-of switcher moved) always wins over a stale local regenerate result
  const view = regenerated && regenerated.as_of === compass.as_of ? regenerated : compass;
  const preFreezeEra = view.mode === null; // an iter-2-era row with no freeze/integrity block recorded

  async function handleConfirm() {
    if (!asOf) return;
    setRegenerating(true);
    setError(null);
    try {
      const result = await regenerateManifest(asOf);
      setRegenerated(result);
      setConfirming(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "regenerate failed");
    } finally {
      setRegenerating(false);
    }
  }

  return (
    <Card data-testid="compass-manifest-strip">
      <CardHeader>
        <CardTitle>Manifest</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {preFreezeEra ? (
          <p className="text-sm text-text-muted" data-testid="compass-manifest-pre-freeze-era">
            This manifest predates the freeze/integrity block — no stamps were recorded for it.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2" data-testid="compass-manifest-badges">
              <Badge variant={view.mode === "at_ingest" ? "ok" : "default"}>{view.mode?.replace(/_/g, " ")}</Badge>
              <Badge variant="default">version {view.version}</Badge>
              <Badge variant={view.frozen ? "ok" : "warn"}>{view.frozen ? "frozen" : "not frozen"}</Badge>
              <Badge variant={view.prospective_eligible ? "ok" : "default"} data-testid="compass-manifest-prospective-eligible">
                {view.prospective_eligible ? "prospective-eligible" : "not prospective-eligible"}
              </Badge>
              {view.generation ? (
                <span className="text-xs text-text-faint">
                  Frozen {new Date(view.generation.generated_at).toLocaleString()}
                </span>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs">
              <HashChip label="Engine identity" value={view.generation?.engine_identity ?? null} />
              <HashChip label="Candidate rule" value={view.candidate_rule_hash} />
              <HashChip label="Cohort rule" value={view.cohort_rule_hash} />
              <HashChip label="Manifest config" value={view.manifest_config_hash} />
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-text-muted">
              <span>
                Dataset stamp: <span className="num text-text">{view.dataset?.stamp ?? "—"}</span>
              </span>
              <HashChip label="Universe pool" value={view.universe?.pool_hash ?? null} />
              <span>
                Members: <span className="num text-text">{view.universe?.member_count ?? "—"}</span>
              </span>
              <span>
                Profile: <span className="text-text">{view.universe?.profile ?? "—"}</span>
              </span>
            </div>

            <BasisLine basis={view.basis} />

            <Disclosure
              summary={`Audit table — comparison cohort (${view.comparison_cohort.length}) + near-threshold shadow (${view.near_threshold_shadow.length})`}
            >
              <div className="space-y-4 pt-1">
                <div>
                  <p className="text-xs font-medium text-text">Comparison cohort (non-selected pool)</p>
                  {view.caveats ? (
                    <p className="pt-0.5 text-xs text-text-faint" data-testid="compass-manifest-cohort-semantics">
                      {view.caveats.cohort_semantics}
                    </p>
                  ) : null}
                  <div className="pt-1">
                    <CohortTable rows={view.comparison_cohort} showDisposition />
                  </div>
                </div>
                {/* the shadow section is ALWAYS visible under its explicit research-only label — never
                    silently folded into the comparison cohort table above (Visual Requirements). */}
                <div>
                  <p className="text-xs font-medium text-warn" data-testid="compass-manifest-shadow-label">
                    Near-threshold shadow — research-only substrate, not part of selection or display ranking
                  </p>
                  <div className="pt-1">
                    <CohortTable rows={view.near_threshold_shadow} showDisposition={false} />
                  </div>
                </div>
                {view.caveats ? (
                  <div className="space-y-1 border-t border-border pt-2 text-xs text-text-faint">
                    <p>{view.caveats.evidence}</p>
                    <p>{view.caveats.survivorship}</p>
                    <p>{view.caveats.sector_basis}</p>
                  </div>
                ) : null}
              </div>
            </Disclosure>

            {view.versions.length > 1 ? (
              <div className="space-y-1 text-xs text-text-muted" data-testid="compass-manifest-versions">
                <p className="uppercase tracking-wide text-text-faint">Versions</p>
                <ul className="space-y-0.5">
                  {view.versions.map((v) => (
                    <li key={v.version} className="flex flex-wrap items-center gap-2" data-testid={`compass-manifest-version-${v.version}`}>
                      <span className="num font-medium text-text">v{v.version}</span>
                      <span>{v.mode?.replace(/_/g, " ") ?? "—"}</span>
                      <span>{v.prospective_eligible ? "eligible" : "not eligible"}</span>
                      <span className="text-text-faint">{v.generated_at ?? "—"}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {asOf ? (
              <button
                type="button"
                onClick={() => setConfirming(true)}
                disabled={regenerating}
                data-testid="compass-manifest-regenerate-button"
                className={cn(
                  "inline-flex h-8 items-center gap-2 rounded-md border px-3 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
                  regenerating ? "cursor-not-allowed border-border text-text-faint" : "border-warn text-warn hover:bg-surface-2",
                )}
              >
                <RotateCcw className="h-3.5 w-3.5" aria-hidden />
                Regenerate manifest
              </button>
            ) : (
              <p className="text-xs text-text-faint" data-testid="compass-manifest-regenerate-unavailable">
                Regenerate is available only for a stored historical date — step the as-of switcher off
                &quot;Latest&quot; first.
              </p>
            )}
          </>
        )}
      </CardContent>

      {confirming && asOf ? (
        <RegenerateConfirmModal
          asOf={asOf}
          regenerating={regenerating}
          error={error}
          onCancel={() => {
            setConfirming(false);
            setError(null);
          }}
          onConfirm={handleConfirm}
        />
      ) : null}
    </Card>
  );
}

/** The J-69-pattern confirm modal (Card + fixed overlay, persistently-visible Confirm button outside any
 *  scroll region — there is no Dialog primitive in this project). Colocated with its caller, mirroring
 *  `RebuildConfirmModal` (apps/frontend/app/data/page.tsx). */
function RegenerateConfirmModal({
  asOf,
  regenerating,
  error,
  onCancel,
  onConfirm,
}: {
  asOf: string;
  regenerating: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(10,14,20,0.8)] p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Confirm manifest regenerate"
      data-testid="compass-manifest-regenerate-confirm-modal"
    >
      <Card className="w-full max-w-lg p-0 shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-warn">
            <RotateCcw className="h-4 w-4" aria-hidden />
            Confirm manifest regenerate
          </h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancel"
            className="rounded p-1 text-text-faint transition hover:bg-surface-2 hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div className="max-h-[55vh] space-y-3 overflow-y-auto p-4 text-sm">
          <p className="text-text-muted">
            This mints a NEW manifest version for {asOf} from the current selection rule and config. The
            existing version is never touched, changed, or deleted — it stays byte-identical and readable.
          </p>
          <ul className="list-disc space-y-1 pl-5 text-xs text-text-faint">
            <li>The new version is never eligible for the future prospective study — only a live freeze&apos;s version 1 can ever be.</li>
            <li>Both versions remain listed with their own stamps afterward.</li>
          </ul>
          {error ? (
            <p role="alert" className="flex items-center gap-2 text-xs text-neg">
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
              {error}
            </p>
          ) : null}
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex h-9 items-center rounded-md border border-border px-4 text-sm text-text-muted transition hover:border-border-strong hover:text-text focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={regenerating}
            data-testid="compass-manifest-regenerate-confirm-button"
            className={cn(
              "inline-flex h-9 items-center gap-2 rounded-md border border-warn bg-warn/10 px-4 text-sm font-semibold text-warn transition hover:bg-warn/20 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent",
              regenerating && "cursor-not-allowed opacity-60",
            )}
          >
            {regenerating ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <RotateCcw className="h-4 w-4" aria-hidden />}
            {regenerating ? "Regenerating…" : "Regenerate manifest"}
          </button>
        </div>
      </Card>
    </div>
  );
}
