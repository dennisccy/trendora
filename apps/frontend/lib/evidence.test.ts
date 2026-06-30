/**
 * Unit tests for the inline evidence-badge status resolver (lib/evidence.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/evidence.test.ts
 *
 * The crux (goal.md anti-goal — nothing "Proven" without a PASS-backed ledger entry; fail-safe default):
 *   (a) a signal ABSENT from the served proven map reads "Not yet proven" with NO link;
 *   (b) a null/undefined map (the fetch failed, or the ledger is empty) reads "Not yet proven";
 *   (c) a PRESENT, proven signal reads "Proven" and links to its `/evidence` backing entry;
 *   (d) a present-but-not-`proven` row is still treated as "Not yet proven" (defensive).
 */
import assert from "node:assert";

import {
  NOT_PROVEN_LABEL,
  PROVEN_LABEL,
  SCORE_SIGNALS,
  claimSurface,
  evidenceAnchor,
  formatEvidencePct,
  formatPValue,
  proofFieldsFor,
  regimeLabel,
  resolveEvidenceStatus,
  type CertifiedClaim,
  type ProvenSignal,
} from "./evidence.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

function provenRow(signal: string): ProvenSignal {
  return {
    signal,
    claim: { kind: "factor", factor: signal, decile: 10, horizon: 20 },
    register_date: "2024-06-01",
    horizon: 20,
    cohort_n: 42,
    control_n: 40,
    verdict: { status: "PASS", reason: "certified", control_excess: 0.018, holdout_edge: 0.031 },
    proven: true,
    forward_walk: null,
  };
}

// --- (a) absent signal => "Not yet proven", no link (the empty-ledger reality this iteration) ----------
check("a signal absent from the proven map reads 'Not yet proven' with no link", () => {
  const status = resolveEvidenceStatus("leadership_score", {});
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, NOT_PROVEN_LABEL);
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
  assert.strictEqual(status.claim, null);
});

// --- (b) null/undefined map (fetch failed / empty ledger) => fail-safe "Not yet proven" ----------------
check("a null or undefined proven map falls back to 'Not yet proven' (fail-safe)", () => {
  for (const map of [null, undefined]) {
    const status = resolveEvidenceStatus("risk_score", map);
    assert.strictEqual(status.proven, false);
    assert.strictEqual(status.label, "Not yet proven");
    assert.strictEqual(status.href, null);
  }
});

// --- (c) present & proven => "Proven" linking to the /evidence backing entry --------------------------
check("a present, proven signal reads 'Proven' and links to its /evidence backing entry", () => {
  const map = { leadership_score: provenRow("leadership_score") };
  const status = resolveEvidenceStatus("leadership_score", map);
  assert.strictEqual(status.proven, true);
  assert.strictEqual(status.label, PROVEN_LABEL);
  assert.strictEqual(status.label, "Proven");
  assert.strictEqual(status.href, "/evidence#signal-leadership_score");
  assert.ok(status.href!.startsWith("/evidence"), "the proven badge must link into /evidence");
  assert.strictEqual(status.claim?.register_date, "2024-06-01");
  assert.strictEqual(status.claim?.verdict.control_excess, 0.018);
});

// --- (d) present but NOT proven => defensively "Not yet proven" ----------------------------------------
check("a present row that is not `proven` is still treated as 'Not yet proven'", () => {
  const row = { ...provenRow("entry_quality_score"), proven: false };
  const status = resolveEvidenceStatus("entry_quality_score", { entry_quality_score: row });
  assert.strictEqual(status.proven, false);
  assert.strictEqual(status.label, "Not yet proven");
  assert.strictEqual(status.href, null);
});

// --- evidenceAnchor is the stable claim→surface linkback target ---------------------------------------
check("evidenceAnchor builds the stable per-signal ledger anchor", () => {
  assert.strictEqual(evidenceAnchor("risk_score"), "/evidence#signal-risk_score");
});

// --- SCORE_SIGNALS — the single shared score→signal map (de-duped in iter-2) ---------------------------
check("SCORE_SIGNALS maps each score to its canonical factor-catalog signal key", () => {
  assert.strictEqual(SCORE_SIGNALS.leadership, "leadership_score");
  assert.strictEqual(SCORE_SIGNALS.entry_quality, "entry_quality_score");
  assert.strictEqual(SCORE_SIGNALS.risk, "risk_score");
});

// ======================================================================================================
// J-02 proof drill-down — `proofFieldsFor` reads the backing claim VERBATIM (the iter-2 PRIMARY contract).
// The values below MIRROR the real certified leadership_score entry the post-decompose gate wrote, so the
// test pins the displayed-numbers-are-correct anti-goal: what the panel shows must equal the served entry.
// ======================================================================================================

/** A proven row mirroring the REAL ledger entry (holdout edge / p-value / control excess / register date /
 *  cohort_n the gate certified for leadership_score), so the proof-field extraction is pinned to reality. */
function provenLeadershipRow(): ProvenSignal {
  return {
    signal: "leadership_score",
    claim: {
      kind: "factor",
      factor: "leadership_score",
      slice_kind: "decile",
      decile: 10,
      horizon: 20,
      direction: "positive",
      signal: "leadership_score",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 12297,
    control_n: 1137,
    verdict: {
      status: "PASS",
      reason: "certified out-of-sample",
      holdout_edge: 0.06359100763913017,
      control_excess: 0.06359100763913017,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

// --- (e) proven => the proof fields are read VERBATIM, with the stable claim id + /evidence anchor -------
check("proofFieldsFor reads the backing claim verbatim for a proven signal", () => {
  const fields = proofFieldsFor("leadership_score", { leadership_score: provenLeadershipRow() });
  assert.ok(fields, "a proven signal must yield proof fields");
  assert.strictEqual(fields!.signal, "leadership_score");
  assert.strictEqual(fields!.status, "PASS");
  // every numeric is the referee's value EXACTLY (no recompute, no rounding in the data layer)
  assert.strictEqual(fields!.holdoutEdge, 0.06359100763913017);
  assert.strictEqual(fields!.pValue, 0.0004997501249375312);
  assert.strictEqual(fields!.controlExcess, 0.06359100763913017);
  assert.strictEqual(fields!.cohortN, 12297);
  assert.strictEqual(fields!.registerDate, "2026-06-30");
  // the stable certified-claim id + the backing /evidence anchor a "Proven" badge round-trips to
  assert.strictEqual(fields!.claimId, "leadership_score · registered 2026-06-30");
  assert.strictEqual(fields!.href, "/evidence#signal-leadership_score");
});

// --- (f) FAIL-SAFE: an unproven / absent / null-map signal yields NO proof fields (no empty panel) ------
check("proofFieldsFor returns null for an absent, null-map, or not-`proven` signal (fail-safe)", () => {
  // absent from the map (the Entry Quality / Risk reality this iteration)
  assert.strictEqual(proofFieldsFor("entry_quality_score", { leadership_score: provenLeadershipRow() }), null);
  // null / undefined map (fetch failed / empty ledger)
  assert.strictEqual(proofFieldsFor("leadership_score", null), null);
  assert.strictEqual(proofFieldsFor("leadership_score", undefined), null);
  // present but explicitly not `proven` (defensive — never trust a non-proven row)
  const notProven = { ...provenLeadershipRow(), proven: false };
  assert.strictEqual(proofFieldsFor("leadership_score", { leadership_score: notProven }), null);
});

// --- (g) the display formatters — exact strings (the panel re-formats; it fabricates nothing) -----------
check("formatEvidencePct renders a signed percent (and an em dash for a missing value)", () => {
  assert.strictEqual(formatEvidencePct(0.06359100763913017), "+6.36%"); // the real holdout edge / control excess
  assert.strictEqual(formatEvidencePct(-0.004), "-0.40%");
  assert.strictEqual(formatEvidencePct(0), "+0.00%");
  assert.strictEqual(formatEvidencePct(null), "—");
  assert.strictEqual(formatEvidencePct(undefined), "—");
  assert.strictEqual(formatEvidencePct(Number.NaN), "—");
});

check("formatPValue renders the p-value to 4 significant figures (with a small/missing fallback)", () => {
  assert.strictEqual(formatPValue(0.0004997501249375312), "0.0004998"); // the real certified p-value
  assert.strictEqual(formatPValue(0.05), "0.05");
  assert.strictEqual(formatPValue(0.0000000001), "< 0.0001");
  assert.strictEqual(formatPValue(null), "—");
  assert.strictEqual(formatPValue(undefined), "—");
});

// ======================================================================================================
// J-04 regime-conditioned evidence — the ClaimRow regime label + the honest non-score title/linkback.
// The row below MIRRORS the real 2nd ledger entry the post-decompose gate certified (Breakout-watch ×
// Risk-on event-study, signal: null), so these pin the J-04 display contract AND the J-05 no-regression
// invariant (the leadership score row's title + linkback stay byte-identical).
// ======================================================================================================

/** A certified (PASS) row mirroring the REAL iter-4 2nd ledger entry: the Breakout-watch setup's
 *  event-study cohort sliced to the named `Risk-on` regime. It deliberately carries NO `signal` (it backs
 *  no per-stock score badge — it is regime-conditioned evidence in its own right). */
function eventStudyRegimeRow(): CertifiedClaim {
  return {
    signal: null,
    claim: {
      kind: "event-study",
      subject: "Breakout-watch",
      slice_kind: "regime",
      regime: "Risk-on",
      view: "pooled",
      horizon: 20,
      direction: "positive",
    },
    register_date: "2026-06-30",
    horizon: 20,
    cohort_n: 4720,
    control_n: 414,
    verdict: {
      status: "PASS",
      reason: "certified out-of-sample (Risk-on)",
      holdout_edge: 0.06124590639955655,
      control_excess: 0.06124590639955655,
      p_value: 0.0004997501249375312,
    },
    proven: true,
    forward_walk: null,
  };
}

// --- (h) regime label — read VERBATIM from the cohort's own `regime` selector when present --------------
check("regimeLabel returns the cohort's regime verbatim for a regime-conditioned claim", () => {
  assert.strictEqual(regimeLabel(eventStudyRegimeRow()), "Risk-on");
});

// --- (i) regime label is HIDDEN (null) for a score claim with no regime (leadership must look unchanged) -
check("regimeLabel returns null for a score claim that carries no regime (label hidden)", () => {
  assert.strictEqual(regimeLabel(provenLeadershipRow()), null);
});

// --- (j) a blank / whitespace / absent regime is treated as absent (no empty 'Regime:' chip) -----------
check("regimeLabel treats a blank, whitespace, or absent regime as hidden", () => {
  const blank = eventStudyRegimeRow();
  blank.claim = { ...blank.claim, regime: "   " };
  assert.strictEqual(regimeLabel(blank), null);
  const absent = eventStudyRegimeRow();
  delete (absent.claim as Record<string, unknown>).regime;
  assert.strictEqual(regimeLabel(absent), null);
});

// --- (k) score row title + linkback stay BYTE-IDENTICAL (J-05 must not regress) ------------------------
check("claimSurface keeps the score row's signal-key title + 'Stocks leaderboard' linkback byte-identical", () => {
  const surface = claimSurface(provenLeadershipRow());
  assert.strictEqual(surface.title, "leadership_score"); // the signal key, rendered in the mono `num` style
  assert.strictEqual(surface.titleIsSignalKey, true);
  assert.strictEqual(surface.subtitle, null);
  assert.strictEqual(surface.href, "/stocks");
  assert.strictEqual(surface.label, "Stocks leaderboard"); // "Backs: Stocks leaderboard →" — unchanged
});

// --- (l) signal-less event-study claim → HONEST title + a NON-leaderboard linkback ----------------------
check("claimSurface gives a signal-less event-study claim an honest title + a non-leaderboard linkback", () => {
  const surface = claimSurface(eventStudyRegimeRow());
  // an honest, meaningful title — NEVER the misleading "Unmapped signal"
  assert.strictEqual(surface.title, "Breakout-watch setup");
  assert.notStrictEqual(surface.title, "Unmapped signal");
  assert.strictEqual(surface.titleIsSignalKey, false);
  // framed as historical out-of-sample evidence in the regime (never a buy/return promise)
  assert.strictEqual(surface.subtitle, "Out-of-sample edge in the Risk-on regime");
  // the linkback is honest — its Research event-study lab, NOT the Stocks leaderboard
  assert.strictEqual(surface.href, "/research/event-study");
  assert.strictEqual(surface.label, "Research event-study lab");
  assert.notStrictEqual(surface.label, "Stocks leaderboard");
});

console.log(`\n${passed} evidence-badge resolver checks passed.`);
