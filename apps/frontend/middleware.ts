import { NextResponse, type NextRequest } from "next/server";

import { ASOF_HEADER, ASOF_PARAM, isValidIsoDate } from "@/lib/dates";

/**
 * J-83 — server-aware seeding of the ONE global as-of state.
 *
 * The as-of state lives in the client `AsOfProvider`, whose lazy `useState` initializer reads the URL's
 * `?asof` via `window` — but `window` is undefined during SSR, so a historical `?asof=D` deep link
 * server-renders at "latest" while the client first-paints at D. React 19 flags the divergence as a
 * "hydration failed / server rendered HTML didn't match" error, and the as-of badge/icon and the
 * sidebar `?asof` hrefs visibly flip latest→D on hydration.
 *
 * This middleware closes that gap WITHOUT introducing a second date state: it reads the request's
 * `?asof` query param, and — only when it is a shape-valid `yyyy-MM-dd` — forwards it as the `x-asof`
 * REQUEST header (`ASOF_HEADER`). The server-component root layout (`app/layout.tsx`) reads that header
 * and passes it as `AsOfProvider`'s `initialAsOf`, so the server seeds the SAME as-of the client reads
 * from the URL and the first paints match. The asof-provider stays the SOLE `?asof` reader/writer; the
 * run-list `ready` validate/degrade pass (J-43) still strips an unknown/latest/malformed date.
 *
 * Security/scope: it forwards ONLY `ASOF_PARAM` and ONLY a shape-valid ISO date — never a provider key,
 * never any other query param, never a non-ISO value. An absent/invalid `?asof` forwards no header
 * (the server then seeds "latest", matching the client fallback exactly).
 */
export function middleware(request: NextRequest): NextResponse {
  const raw = request.nextUrl.searchParams.get(ASOF_PARAM);

  // Mirror the client's `readAsofFromUrl` shape gate exactly: only a well-formed ISO date is forwarded.
  // Anything else (missing, malformed, non-ISO) → no header, so the server seeds latest (J-43 degrade
  // still owns "is D a real run?" on the client; the middleware never validates against the run list).
  if (!raw || !isValidIsoDate(raw)) {
    return NextResponse.next();
  }

  // Forward the one shape-valid `?asof` value on the one header. We rewrite the request headers (not the
  // response) so the downstream server component can read it via `next/headers`. No other header is set.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(ASOF_HEADER, raw);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

/**
 * Run on app PAGES only — exclude API routes, Next internals, and static assets so the middleware never
 * runs for a fetch/asset request (it has nothing to forward there and would only add overhead).
 */
export const config = {
  matcher: [
    // Everything except: /api/*, /_next/static/*, /_next/image/*, the favicon, and any file with an
    // extension (static assets like .css/.js/.png/.svg/.ico/.woff…). Matches all real app pages.
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.[^/]+$).*)",
  ],
};
