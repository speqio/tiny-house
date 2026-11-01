import type { NextConfig } from "next";

// three.js necesita transpilación para el bundle de Next.js
const nextConfig: NextConfig = {
  transpilePackages: ["three"],
  reactStrictMode: true,
};

export default nextConfig;
