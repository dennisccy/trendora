/**
 * Host-aware backend base resolution (J-108). A pure, dependency-free helper so it is unit-testable
 * under the `node lib/*.test.ts` pattern.
 *
 * WHY THIS EXISTS — the readiness-badge "Backend unavailable" trust bug:
 *   `./scripts/dev.sh` bakes `NEXT_PUBLIC_API_URL=http://localhost:<backendPort>` into the frontend, but
 *   ALSO advertises the app at `http://<LAN_IP>:<frontendPort>`. A browser that opened the page at the
 *   LAN-IP origin must NOT fetch "localhost" — "localhost" resolves to the VIEWER's own machine, not the
 *   dev host, so `fetchHealth()` throws and the badge sticks on "Backend unavailable". The fix: when the
 *   configured base points at localhost but the page is opened on a non-localhost host, hit the backend on
 *   the SAME host the page loaded from (its hostname) + the configured backend port.
 *
 * It is a PURE re-resolution of WHERE the backend is — it never fabricates readiness or any served value.
 */

/** Hostnames that mean "this machine" — a base/page on one of these is the local dev path. */
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"]);

function isLocalHost(host: string | null | undefined): boolean {
  return host != null && LOCAL_HOSTS.has(host);
}

/**
 * Resolve the backend API base for a request, host-aware.
 *
 * @param configuredBase the build-time configured base (`NEXT_PUBLIC_API_URL`, default localhost).
 * @param hostname       the page's `window.location.hostname` (undefined/"" during SSR — no swap then).
 * @param port           the configured backend port (`NEXT_PUBLIC_API_PORT`); authoritative when set.
 *
 * Rules, in order:
 *  1. No page host (SSR) -> the configured base verbatim (cannot host-swap).
 *  2. Configured base host is NOT localhost (an explicit operator URL) -> verbatim, authoritative.
 *  3. Page host IS localhost -> the configured base verbatim (the same-host dev path is already correct).
 *  4. Configured base is localhost but the page host is non-localhost (LAN-IP) -> hit the backend on the
 *     page host + the configured backend port (the `port` arg, else the configured base's own port).
 */
export function resolveApiBase(
  configuredBase: string,
  hostname?: string | null,
  port?: string | null,
): string {
  // 1. SSR / no page host -> cannot host-swap; use the configured base verbatim.
  if (!hostname) return configuredBase;

  // Parse the configured base; an unparseable value is returned verbatim (never throws).
  let configured: URL;
  try {
    configured = new URL(configuredBase);
  } catch {
    return configuredBase;
  }

  // 2. An explicit non-localhost backend URL is authoritative — used verbatim.
  if (!isLocalHost(configured.hostname)) return configuredBase;

  // 3. The page itself is on localhost -> the same-host dev path already works; keep the configured base.
  if (isLocalHost(hostname)) return configuredBase;

  // 4. Configured-localhost base opened on a non-localhost (LAN-IP) host: hit the backend on the SAME
  //    host the page loaded from + the configured backend port (so the browser reaches the dev host).
  const backendPort = (port != null && port.trim() !== "") ? port.trim() : configured.port;
  const portSuffix = backendPort ? `:${backendPort}` : "";
  return `${configured.protocol}//${hostname}${portSuffix}`;
}
