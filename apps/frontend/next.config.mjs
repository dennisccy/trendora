/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No ESLint config is shipped for the MVP; UI behaviour is covered by browser QA.
  // Type-checking stays ON (the frontend "test" is `npm run build` = compile + typecheck).
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
