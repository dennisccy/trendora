/**
 * Unit tests for the J-07 / auditor-F3 ambient-refresh failure helper (lib/data-overview-refresh.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   npx tsx lib/data-overview-refresh.test.ts
 * (ops-hardening iter-63, TC-6: this repo's Node 22 install errors ERR_UNKNOWN_FILE_EXTENSION on a
 * plain `node lib/data-overview-refresh.test.ts` invocation for a .ts file; only the `npx tsx` form
 * above actually exits 0 here — the comment previously named the bare `node` form, which does not run.
 * The test logic itself is unchanged and was already correct/green under `npx tsx`.)
 * Pins the helper's three input cases (TC-6): `ok` preserved unchanged, `loading` -> `error`,
 * `error` -> `error`.
 */
import assert from "node:assert";

import { nextStateAfterFetchError, type FetchState } from "./data-overview-refresh.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

check("an 'ok' state is returned UNCHANGED (same reference) on a fetch failure", () => {
  const ok: FetchState<{ n: number }> = { kind: "ok", data: { n: 42 } };
  const result = nextStateAfterFetchError(ok);
  assert.strictEqual(result, ok); // same object reference -- proves it is untouched, not just equal
  assert.deepStrictEqual(result, { kind: "ok", data: { n: 42 } });
});

check("a 'loading' state (initial mount, no data yet) becomes 'error'", () => {
  const loading: FetchState<{ n: number }> = { kind: "loading" };
  assert.deepStrictEqual(nextStateAfterFetchError(loading), { kind: "error" });
});

check("an 'error' state stays 'error' (a repeated failure is not silently swallowed)", () => {
  const error: FetchState<{ n: number }> = { kind: "error" };
  assert.deepStrictEqual(nextStateAfterFetchError(error), { kind: "error" });
});

console.log(`\n${passed} passed`);
