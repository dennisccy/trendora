"use client";

import { AlertTriangle } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Disclosure } from "@/components/ui/disclosure";
import type { CompassResponse } from "@/lib/api";

/** J-03 (goal-market-compass iter-2): the plain-English summary card. Every sentence is rendered
 *  VERBATIM from `GET /api/compass`'s `narrative.sentences` — the frontend assembles no wording,
 *  selects no word, and evaluates no threshold; it only re-displays served text plus its cited
 *  facts (single source of truth — no client-composed wording). */
export function CompassSummaryCard({ compass }: { compass: CompassResponse | null }) {
  if (compass === null) {
    return (
      <Card
        className="flex items-center gap-3 border-neg bg-surface p-4 text-sm text-neg"
        data-testid="compass-summary-unavailable"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        Summary is unavailable — backend not reachable.
      </Card>
    );
  }

  const { sentences } = compass.narrative;

  return (
    <Card data-testid="compass-summary-card">
      <CardHeader>
        <CardTitle>Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5 text-sm text-text">
          {sentences.map((sentence) => (
            <p key={sentence.template_id} data-testid={`compass-sentence-${sentence.template_id}`}>
              {sentence.text}
            </p>
          ))}
        </div>
        <Disclosure summary="Show cited facts">
          <ul className="space-y-2 pt-1">
            {sentences.map((sentence) => (
              <li key={sentence.template_id} className="text-xs text-text-muted">
                <span className="font-medium text-text">{sentence.template_id}</span>
                {sentence.facts.length === 0 ? (
                  <span className="text-text-faint"> — no cited facts.</span>
                ) : (
                  <ul className="ml-3 mt-0.5 space-y-0.5">
                    {sentence.facts.map((fact) => (
                      <li key={fact.name} className="flex items-center gap-2">
                        <span className="text-text-faint">{fact.name}:</span>
                        <span className="num text-text">{String(fact.value)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </Disclosure>
      </CardContent>
    </Card>
  );
}
