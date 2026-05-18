import type { NextConfig } from "next";

/**
 * Deep Research Platform - Next.js Configuration
 *
 * WHY explicit config:
 * - Documents all active Next.js features
 * - Controls experimental flags deliberately
 * - Environment variable validation at build time
 */
const nextConfig: NextConfig = {
  // Strict React mode — catches lifecycle bugs early
  reactStrictMode: true,

  // Enable standalone output for Docker multi-stage builds
  output: "standalone",

  // Environment variables exposed to the browser must be declared here
  // (NEXT_PUBLIC_* vars are automatically inlined by Next.js)
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version ?? "0.0.0",
  },

  // Image domains for next/image (add API domains here as needed)
  images: {
    remotePatterns: [],
  },

  // Experimental features
  experimental: {
    // Typed routes — catch invalid href values at compile time
    typedRoutes: true,
  },
};

export default nextConfig;
