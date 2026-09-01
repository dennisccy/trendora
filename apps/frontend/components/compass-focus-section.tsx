"use client";

import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Disclosure } from "@/components/ui/disclosure";
import type { ChecklistVerdict, CompassCandidate, CompassResponse, WhyNotEntry } from "@/lib/api";

const VERDICT_VARIANT: Record<ChecklistVerdict, "ok" | "danger" | "default" | "warn"> = {
  Pass: "ok",
  Miss: "danger",
  Supportive: "ok",
  Neutral: "default",
  Unknown: "warn",
  NA: "default",
};

/** One next-session candidate card. Every field — the words, the reasons, the cautions, the
 *  checklist verdicts, and the "what would change this" rows — is rendered VERBATIM from the
 *  served `CompassCandidate`. No rule table or threshold lives in this file (TC-18): the checklist
 *  and what-would-change rows map only over served `condition`/`threshold`/`actual`/`verdict`/`met`
 *  fields. */
function CandidateCard({ candidate }: { candidate: CompassCandidate }) {
  return (
    <Card className="space-y-3 p-4" data-testid={`compass-candidate-${candidate.ticker}`}>
      <h3 className="num text-base font-semibold text-text">{candidate.ticker}</h3>

      <div className="grid gap-2 text-xs sm:grid-cols-3">
        <div>
          <p className="uppercase tracking-wide text-text-faint">Leadership</p>
          <p className="text-text">
            {candidate.leadership_word}{" "}
            <span className="num text-text-muted">({candidate.leadership_score.toFixed(1)})</span>
          </p>
        </div>
        <div>
          <p className="uppercase tracking-wide text-text-faint">Entry</p>
          <p className="text-text">
            {candidate.entry_word}{" "}
            <span className="num text-text-muted">({candidate.entry_quality_score.toFixed(1)})</span>
          </p>
        </div>
        <div>
          <p className="uppercase tracking-wide text-text-faint">Risk</p>
          <p className="text-text">
            {candidate.risk_word}{" "}
            <span className="num text-text-muted">({candidate.risk_score.toFixed(1)})</span>
          </p>
        </div>
      </div>

      <div className="space-y-1">
        <p className="text-xs uppercase tracking-wide text-text-faint">Why</p>
        <ul className="space-y-0.5 text-xs text-text-muted">
          {candidate.reasons.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      </div>

      {candidate.cautions.length > 0 ? (
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-wide text-warn">Cautions</p>
          <ul className="space-y-0.5 text-xs text-warn">
            {candidate.cautions.map((caution, index) => (
              <li key={index}>{caution}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <Disclosure summary="Eligibility checklist">
        <ul className="space-y-1 pt-1">
          {candidate.checklist.map((row, index) => (
            <li key={index} className="flex items-center justify-between gap-2 text-xs">
              <span className="text-text-muted">{row.condition}</span>
              <span className="flex items-center gap-2">
                <span className="num text-text-faint">
                  {row.actual.toFixed(1)} vs {row.threshold.toFixed(1)}
                </span>
                <Badge variant={VERDICT_VARIANT[row.verdict]}>{row.verdict}</Badge>
              </span>
            </li>
          ))}
        </ul>
      </Disclosure>

      <Disclosure summary="What would change this">
        <ul className="space-y-1 pt-1">
          {candidate.what_would_change.map((row, index) => (
            <li key={index} className="flex items-center justify-between gap-2 text-xs text-text-muted">
              <span>{row.condition}</span>
              <span className="num">
                {row.actual.toFixed(1)} vs {row.threshold.toFixed(1)} — {row.met ? "met" : "not met"}
              </span>
            </li>
          ))}
        </ul>
      </Disclosure>

      <p className="text-xs text-text-faint">
        <span className="uppercase tracking-wide">Invalidation: </span>
        {candidate.invalidation}
      </p>
    </Card>
  );
}

/** One why-not entry's reason-appropriate lead-in sentence (J-14) — re-renders served `reason` /
 *  `cap_rank` / `cap` fields verbatim, applies no threshold and computes no distance of its own. A
 *  cap-excluded entry names its rank among the above-floor names and the configured cap; a
 *  below-floor entry gets no separate lead-in (its `failed_conditions` list, below, already names the
 *  leadership floor first). */
function WhyNotLeadIn({ entry }: { entry: WhyNotEntry }) {
  if (entry.reason !== "excluded_by_cap" || entry.cap_rank === null || entry.cap === null) {
    return null;
  }
  return (
    <span className="text-text-muted">
      {" "}
      — ranked #{entry.cap_rank} of the above-floor names, cap {entry.cap}
      {entry.failed_conditions.length === 0 ? " — passed every qualifier, cut only by the focus-list cap." : ""}
    </span>
  );
}

function WhyNotList({ entries }: { entries: WhyNotEntry[] }) {
  if (entries.length === 0) {
    return <p className="pt-1 text-xs text-text-faint">No near-miss names this session.</p>;
  }
  return (
    <ul className="space-y-2 pt-1">
      {entries.map((entry) => (
        <li key={entry.ticker} className="text-xs" data-testid={`compass-why-not-${entry.ticker}`}>
          <span className="num font-medium text-text">{entry.ticker}</span>
          <WhyNotLeadIn entry={entry} />
          {entry.failed_conditions.length > 0 ? (
            <ul className="ml-3 mt-0.5 space-y-0.5 text-text-muted">
              {entry.failed_conditions.map((failed, index) => (
                <li key={index}>
                  {failed.condition}: {failed.actual.toFixed(1)} vs {failed.threshold.toFixed(1)} (distance{" "}
                  {failed.distance.toFixed(1)}){failed.gating ? "" : " — advisory"}
                </li>
              ))}
            </ul>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

/** J-04 (goal-market-compass iter-2): the Next-session focus section. The candidate set, its
 *  reasons/cautions/checklist, and the why-not list are all slices of the ONE served
 *  `compass.evaluate_selection` trace (`GET /api/compass`'s `selection` block) — this component
 *  re-renders served structures and implements no rule. Framed as "worth monitoring next session",
 *  never as advice (anti-goal AG-2); the near-threshold shadow cohort (J-05/J-06) has no field in
 *  this payload and so cannot appear here. */
export function CompassFocusSection({ compass }: { compass: CompassResponse | null }) {
  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-focus-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        Next-session focus is unavailable — backend not reachable.
      </Card>
    );
  }

  const { selection } = compass;

  return (
    <Card data-testid="compass-focus-section">
      <CardHeader>
        <CardTitle>Next-session focus</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {selection.candidates.length === 0 ? (
          <p className="text-sm text-text-muted" data-testid="compass-focus-empty">
            {selection.candidates_empty_reason ?? "No names clear the focus bar this session."}
          </p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2" data-testid="compass-candidate-list">
            {selection.candidates.map((candidate) => (
              <CandidateCard key={candidate.ticker} candidate={candidate} />
            ))}
          </div>
        )}
        <Disclosure
          summary={`Not priority (${selection.why_not.length} shown of ${
            selection.why_not_totals.excluded_by_cap_uncapped + selection.why_not_totals.below_floor_in_band_uncapped
          } held back — ${selection.why_not_totals.excluded_by_cap_uncapped} cap-excluded, ${
            selection.why_not_totals.below_floor_in_band_uncapped
          } below-floor near-miss)`}
        >
          <WhyNotList entries={selection.why_not} />
        </Disclosure>
      </CardContent>
    </Card>
  );
}
