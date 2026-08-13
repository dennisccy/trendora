/**
 * Unit tests for the J-04/J-07 readiness-badge/preflight-banner LIVE staleness tick derivation
 * (lib/staleness-tick.ts). No test framework is installed in this frontend; these run under Node's
 * native TS type-stripping:
 *   node lib/staleness-tick.test.ts
 * (mirrors `lib/staleness-annotation.test.ts`'s existing convention -- see that file's own header note
 * on the documented dev-box `node lib/*.test.ts` limitation.)
 *
 * ops-hardening iter-78 (iter-77/d): `stale_for_s` previously only updated on poll landing, so the
 * "as of Ns ago" annotation could read stale for up to the full poll-idle interval before the next poll
 * refreshed it. `deriveLiveStaleForS` re-derives the live value between polls; these tests cover TC-3
 * (a positive base ticks up smoothly) and TC-4 (null/0/negative/non-finite bases never start ticking,
 * so `formatStaleAnnotation`'s own null-rendering guards keep applying to the derived value unchanged).
 */
import assert from "node:assert";

import { deriveLiveStaleForS } from "./staleness-tick.ts";
import { formatStaleAnnotation } from "./staleness-annotation.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

check("a positive base ticks up by the elapsed client seconds since receipt", () => {
  const receivedAt = 1_000_000;
  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt), 5);
  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt + 10_000), 15);
  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt + 500), 5.5);
});

check(
  "TC-3: 'as of 5s ago' from a landed poll, 10 more seconds elapse with no new poll -> ~15s, not frozen",
  () => {
    const receivedAt = 2_000_000;
    const live = deriveLiveStaleForS(5, receivedAt, receivedAt + 10_000);
    assert.strictEqual(formatStaleAnnotation(live), "as of 15s ago");
  },
);

check("a null base (no poll landed yet / failed poll) never starts ticking, whatever the elapsed time", () => {
  assert.strictEqual(deriveLiveStaleForS(null, 1_000_000, 2_000_000), null);
  assert.strictEqual(deriveLiveStaleForS(null, null, 2_000_000), null);
});

check("TC-4: stale_for_s === 0 (fresh/synchronous compute) never starts ticking upward", () => {
  const receivedAt = 3_000_000;
  const live = deriveLiveStaleForS(0, receivedAt, receivedAt + 60_000);
  assert.strictEqual(live, 0);
  assert.strictEqual(formatStaleAnnotation(live), null);
});

check("TC-4: staleForS === null (failed poll) renders nothing even as the tick timer fires", () => {
  const live = deriveLiveStaleForS(null, null, 5_000_000);
  assert.strictEqual(formatStaleAnnotation(live), null);
});

check("a negative base (defensive, unexpected payload shape) is never ticked into a positive number", () => {
  const receivedAt = 4_000_000;
  const live = deriveLiveStaleForS(-3, receivedAt, receivedAt + 60_000);
  assert.strictEqual(live, -3);
  assert.strictEqual(formatStaleAnnotation(live), null);
});

check("a non-finite base (NaN/Infinity) is passed through unchanged, never fabricated into a number", () => {
  assert.strictEqual(deriveLiveStaleForS(Number.NaN, 1_000_000, 2_000_000), Number.NaN);
  assert.strictEqual(
    deriveLiveStaleForS(Number.POSITIVE_INFINITY, 1_000_000, 2_000_000),
    Number.POSITIVE_INFINITY,
  );
});

check("a positive base with a missing/invalid receipt anchor falls back to the base, unticked", () => {
  assert.strictEqual(deriveLiveStaleForS(5, null, 2_000_000), 5);
  assert.strictEqual(deriveLiveStaleForS(5, Number.NaN, 2_000_000), 5);
});

check("elapsed time never goes negative even if `now` somehow precedes the receipt timestamp", () => {
  const receivedAt = 5_000_000;
  assert.strictEqual(deriveLiveStaleForS(5, receivedAt, receivedAt - 2_000), 5);
});

console.log(`${passed} passed`);
