/**
 * Unit tests for the J-108 host-aware backend base resolver (lib/api-base.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/api-base.test.ts
 * They assert EXACT resolved strings for the four cases that drive the readiness-badge trust fix:
 *  1. SSR / no page host           -> the configured base verbatim (no host swap possible).
 *  2. localhost-config + LAN host  -> the page host + the configured backend port (NEXT_PUBLIC_API_PORT).
 *  3. explicit non-localhost URL    -> used verbatim (an operator-set NEXT_PUBLIC_API_URL is authoritative).
 *  4. localhost-config + localhost  -> stays localhost (the same-host dev path is unchanged).
 */
import assert from "node:assert";

import { resolveApiBase } from "./api-base.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- 1. SSR / no page host: cannot host-swap -> configured base verbatim ---------------------------

check("no hostname (SSR) returns the configured base verbatim", () => {
  assert.strictEqual(resolveApiBase("http://localhost:8000", undefined, "8000"), "http://localhost:8000");
});

check("empty hostname (SSR) returns the configured base verbatim", () => {
  assert.strictEqual(resolveApiBase("http://localhost:8000", "", "8000"), "http://localhost:8000");
});

// --- 2. localhost-config + non-localhost page host -> page host + configured backend port ---------

check("localhost config opened at a LAN-IP host resolves to that host + NEXT_PUBLIC_API_PORT", () => {
  assert.strictEqual(
    resolveApiBase("http://localhost:8000", "192.168.1.42", "8000"),
    "http://192.168.1.42:8000",
  );
});

check("the explicit port arg (NEXT_PUBLIC_API_PORT) wins over the configured base's port", () => {
  assert.strictEqual(
    resolveApiBase("http://localhost:8000", "192.168.1.42", "8123"),
    "http://192.168.1.42:8123",
  );
});

check("falls back to the configured base's port when no port arg is given", () => {
  assert.strictEqual(
    resolveApiBase("http://localhost:8000", "10.0.0.5", undefined),
    "http://10.0.0.5:8000",
  );
});

check("127.0.0.1-configured base opened at a LAN host also host-swaps", () => {
  assert.strictEqual(
    resolveApiBase("http://127.0.0.1:8000", "192.168.0.7", "8000"),
    "http://192.168.0.7:8000",
  );
});

// --- 3. explicit non-localhost NEXT_PUBLIC_API_URL -> verbatim ------------------------------------

check("an explicit non-localhost API URL is used verbatim even from a LAN host", () => {
  assert.strictEqual(
    resolveApiBase("https://api.trendora.example", "192.168.1.42", "8000"),
    "https://api.trendora.example",
  );
});

check("an explicit non-localhost API URL with a port is used verbatim", () => {
  assert.strictEqual(
    resolveApiBase("https://api.example.com:9000", "192.168.1.42", "8000"),
    "https://api.example.com:9000",
  );
});

// --- 4. localhost-config + localhost page host -> stays localhost (unchanged dev path) -------------

check("localhost config opened at localhost stays localhost", () => {
  assert.strictEqual(resolveApiBase("http://localhost:8000", "localhost", "8000"), "http://localhost:8000");
});

check("localhost config opened at 127.0.0.1 stays the configured localhost base", () => {
  assert.strictEqual(resolveApiBase("http://localhost:8000", "127.0.0.1", "8000"), "http://localhost:8000");
});

// --- robustness: an unparseable configured base never crashes (returns verbatim) ------------------

check("an unparseable configured base is returned verbatim (never throws)", () => {
  assert.strictEqual(resolveApiBase("not a url", "192.168.1.42", "8000"), "not a url");
});

console.log(`\n${passed} passed`);
