/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No ESLint config is shipped for the MVP; UI behaviour is covered by browser QA.
  // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
  eslint: { ignoreDuringBuilds: true },
  // `NEXT_DIST_DIR` lets a verification build write to a THROWAWAY dir instead of `.next`, so a CI/dev
  // typecheck-build never clobbers a running `next dev` server's `.next` (defaults to `.next`).
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
