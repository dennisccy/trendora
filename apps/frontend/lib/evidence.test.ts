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
  evidenceAnchor,
  resolveEvidenceStatus,
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

console.log(`\n${passed} evidence-badge resolver checks passed.`);
