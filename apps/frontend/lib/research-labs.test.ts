/**
 * Unit tests for the J-113 Research hub reading order (lib/research-labs.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/research-labs.test.ts
 *
 * The J-113 crux (hub reorder so regime/phase/factor labs lead the reading order): the single ordered
 * source the hub grid maps over must be EXACTLY the reordered ten-lab list — no lab added, removed, or
 * renamed; every route still present and deep-linkable. These tests assert that:
 *   (a) the hub renders exactly the ten canonical lab routes (none dropped, none duplicated);
 *   (b) the reading order is exactly Factor → Regime → Phase&Severity → Regime×Phase×Factor →
 *       Regime×Setup×Pattern → Severity-velocity → Multi-factor → event study → Recovery-Turn → Downtrend;
 *   (c) every lab keeps a non-empty title + description + a known icon key (presentation, not data);
 *   (d) every href is a distinct `/research/<slug>` route (all reachable + deep-linkable).
 */
import assert from "node:assert";

import { RESEARCH_LABS } from "./research-labs.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// The exact reading order (J-113) by route slug — the spec's ordered list.
const EXPECTED_ORDER = [
  "/research/factor-lab",
  "/research/regime-lab",
  "/research/phase-severity-lab",
  "/research/regime-phase-factor",
  "/research/regime-setup-pattern",
  "/research/severity-velocity",
  "/research/factor-combination",
  "/research/event-study",
  "/research/recovery-turn-edge",
  "/research/downtrend-opportunity",
];

const KNOWN_ICONS = new Set([
  "LineChart",
  "Gauge",
  "Thermometer",
  "Boxes",
  "Layers",
  "Waves",
  "GitCompareArrows",
  "Microscope",
  "TrendingUp",
  "TrendingDown",
]);

// --- (a) exactly the ten canonical routes, none dropped or duplicated ----------------------------

check("the hub lists exactly ten labs", () => {
  assert.strictEqual(RESEARCH_LABS.length, 10);
});

check("the set of routes equals the ten canonical lab routes (no add / drop / rename)", () => {
  const got = new Set(RESEARCH_LABS.map((l) => l.href));
  assert.strictEqual(got.size, 10, "no duplicate route");
  assert.deepStrictEqual([...got].sort(), [...EXPECTED_ORDER].sort());
});

// --- (b) the reading order is EXACTLY the spec's ordered list -------------------------------------

check("the reading order is exactly regime/phase/factor-first then the rest", () => {
  assert.deepStrictEqual(
    RESEARCH_LABS.map((l) => l.href),
    EXPECTED_ORDER,
  );
});

check("Factor Lab leads and Downtrend Opportunity is last", () => {
  assert.strictEqual(RESEARCH_LABS[0].href, "/research/factor-lab");
  assert.strictEqual(RESEARCH_LABS[RESEARCH_LABS.length - 1].href, "/research/downtrend-opportunity");
});

// --- (c) every card has a non-empty title + description + a known icon key ------------------------

check("every lab has a non-empty title, description, and a known icon key", () => {
  RESEARCH_LABS.forEach((l) => {
    assert.ok(l.title.length > 0, `${l.href} has a title`);
    assert.ok(l.description.length > 0, `${l.href} has a description`);
    assert.ok(KNOWN_ICONS.has(l.icon), `${l.href} has a known icon key (${l.icon})`);
  });
});

// --- (d) every href is a distinct /research/<slug> route -----------------------------------------

check("every href is a distinct /research/<slug> route (reachable + deep-linkable)", () => {
  RESEARCH_LABS.forEach((l) => {
    assert.match(l.href, /^\/research\/[a-z-]+$/, `${l.href} is a /research/<slug> route`);
  });
  const slugs = RESEARCH_LABS.map((l) => l.href.split("/").pop());
  assert.strictEqual(new Set(slugs).size, slugs.length, "all slugs distinct");
});

console.log(`\nresearch-labs: ${passed} checks passed`);
