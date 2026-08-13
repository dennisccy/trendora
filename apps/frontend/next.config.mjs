import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// ==== TRENDORA BUILD GUARD (ops-hardening iter-77 audit fix B2) ======================================
// WHY THIS EXISTS: an out-of-band `npx next build` run inside `apps/frontend` as a *verification* step
// (the exact command iter-77's own dev handoff and QA report each record running) rewrote the LIVE
// `.next` that `next start` was serving at that moment. Two distinct harms, both reproduced during the
// iter-77 audit:
//   (1) the verification build carries no `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` (only
//       `scripts/start-frontend.sh` exports them), so Next inlines `lib/api.ts`'s
//       `http://localhost:8000` fallback -- a port NOTHING in this project binds -- and every page then
//       renders the global "Backend unavailable" state while the backend is perfectly healthy;
//   (2) rewriting a dist dir a live `next start` is serving tears that server's assets mid-flight
//       (the iteration's own demo gallery captured five consecutive full-page crash-boundary frames).
// The launcher's build lock cannot serialize this (a bare `next build` is not a launcher invocation) and
// its mtime-based staleness check cannot see it (the foreign build looks perfectly current).
//
// `next.config.mjs` is the ONE file every `next build` must load, whoever invokes it and however -- so
// the guard lives here. It refuses the build with an actionable message instead of letting it corrupt a
// live serving directory. The project already ships throwaway dist dirs (`.next-verify`, `.next-alt-qa`)
// for exactly this; the message names them.
// This is a BUILD-PHASE-ONLY guard: `next start` / `next dev` load this same config and are untouched.
const LIVE_DIST_DIR = ".next";
const SERVING_MARKER = ".trendora-serving";
const PHASE_PRODUCTION_BUILD = "phase-production-build";
// Next resolves a relative `distDir` against the PROJECT dir (where this config lives), not the caller's
// cwd — resolve the same way so the guard reads the same directory Next is about to write.
const PROJECT_DIR = dirname(fileURLToPath(import.meta.url));

/** True iff `pid` is alive AND still looks like a Node/Next server process. The liveness check alone
 *  would be fooled by PID reuse after a server exits without clearing its marker; the `/proc` cmdline
 *  check makes a false "it is still being served" refusal effectively impossible. Hosts without `/proc`
 *  fall back to liveness alone. */
function looksLikeALiveServer(pid) {
  try {
    process.kill(pid, 0);
  } catch (err) {
    // EPERM = the process exists but belongs to another user -> still alive.
    if (err?.code !== "EPERM") return false;
  }
  try {
    const cmdline = readFileSync(`/proc/${pid}/cmdline`, "utf8").replace(/\0/g, " ");
    return /(^|[\s/])(next|npx|node|taskset)(\s|$)/.test(cmdline);
  } catch {
    return true;
  }
}

/** The `{pid, port}` of the process currently SERVING `distDir`, or null when nothing is. Written by
 *  `scripts/start-frontend.sh` immediately before it `exec`s `next start` (so the recorded pid IS the
 *  serving process), and self-invalidating: a marker whose pid is gone reads as "nothing is serving". */
function liveServerOwning(distDir) {
  const markerPath = resolve(PROJECT_DIR, distDir, SERVING_MARKER);
  if (!existsSync(markerPath)) return null;
  let raw;
  try {
    raw = readFileSync(markerPath, "utf8");
  } catch {
    return null;
  }
  const fields = {};
  for (const line of raw.split("\n")) {
    const eq = line.indexOf("=");
    if (eq > 0) fields[line.slice(0, eq)] = line.slice(eq + 1);
  }
  const pid = Number.parseInt(fields.pid ?? "", 10);
  if (!Number.isInteger(pid) || pid <= 0) return null;
  if (!looksLikeALiveServer(pid)) return null;
  return { pid, port: fields.port ?? "unknown" };
}

function assertProductionBuildMayTarget(distDir) {
  // `scripts/start-frontend.sh` sets this for its OWN build. It is not an escape hatch for verification
  // builds: the launcher holds the per-dist-dir build lock, always exports the backend URL, and is the
  // process that will serve the result.
  const launcherBuild = process.env.TRENDORA_LAUNCH_BUILD === "1";
  const serving = liveServerOwning(distDir);

  if (serving && !launcherBuild) {
    throw new Error(
      [
        "",
        `TRENDORA BUILD GUARD: refusing to build into '${distDir}' — it is being SERVED right now`,
        `(next start, pid ${serving.pid}, port ${serving.port}).`,
        "",
        "Rewriting a dist directory a live server is serving tears that server's assets mid-flight:",
        "chunk requests start 404-ing and the app renders a full-page error boundary (ops-hardening",
        "iter-77 audit, finding B1/B2). Build somewhere else instead:",
        "",
        "    NEXT_DIST_DIR=.next-verify npx next build     # verification / typecheck build",
        "",
        "To rebuild what is actually served, restart it through the launcher (it holds the build lock,",
        "exports this project's backend URL, and serves the result itself):",
        "",
        "    scripts/start-frontend.sh",
        "",
        `(If no server is really running, remove the stale marker: rm ${distDir}/${SERVING_MARKER})`,
        "",
      ].join("\n"),
    );
  }

  if (serving && launcherBuild) {
    // A launcher rebuild while ANOTHER launcher serves the same dist dir (two invocations on different
    // ports — `test_concurrent_invocations_never_serve_partial_build`'s shape). Allowed, because the
    // launcher owns this directory's lifecycle and refusing here could deadlock a legitimate restart —
    // but never silently.
    console.warn(
      `[trendora build guard] WARNING: rebuilding '${distDir}' while pid ${serving.pid} is serving it ` +
        `on port ${serving.port} — that server's in-flight asset requests may 404 until it restarts.`,
    );
  }

  if (distDir === LIVE_DIST_DIR && !process.env.NEXT_PUBLIC_API_URL) {
    throw new Error(
      [
        "",
        `TRENDORA BUILD GUARD: refusing to build into the live dist dir '${LIVE_DIST_DIR}' without`,
        "NEXT_PUBLIC_API_URL set.",
        "",
        "Next inlines that value into the client bundle at BUILD time. Without it, lib/api.ts falls back",
        "to http://localhost:8000 — a port nothing in this project binds — and every page renders",
        "'Backend unavailable' against a perfectly healthy backend (ops-hardening iter-77 audit, B1).",
        "",
        "For a verification / typecheck build, target a throwaway dir (never the live one):",
        "",
        "    NEXT_DIST_DIR=.next-verify npx next build",
        "",
        "To (re)build what is actually served, use the launcher — it derives this project's backend port",
        "and exports NEXT_PUBLIC_API_URL/NEXT_PUBLIC_API_PORT for you:",
        "",
        "    scripts/start-frontend.sh",
        "",
      ].join("\n"),
    );
  }
}
// ==== end TRENDORA BUILD GUARD ========================================================================

/** @type {(phase: string) => import('next').NextConfig} */
export default function nextConfig(phase) {
  // `NEXT_DIST_DIR` lets a verification build write to a THROWAWAY dir instead of `.next`, so a CI/dev
  // typecheck-build never clobbers a running server's `.next` (defaults to `.next`).
  const distDir = process.env.NEXT_DIST_DIR || LIVE_DIST_DIR;

  // Build phase only — serving (`next start`) and `next dev` load this same config untouched.
  if (phase === PHASE_PRODUCTION_BUILD || process.env.NEXT_PHASE === PHASE_PRODUCTION_BUILD) {
    assertProductionBuildMayTarget(distDir);
  }

  return {
    reactStrictMode: true,
    // No ESLint config is shipped for the MVP; UI behaviour is covered by browser QA.
    // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
    eslint: { ignoreDuringBuilds: true },
    distDir,
  };
}
