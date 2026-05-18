/**
 * ============================================
 * Deep Research Platform - Shared Feature Flag Contracts
 * ============================================
 * Frontend-side feature flag definitions, mirroring backend FeatureFlag enum.
 * Used by the frontend FeatureFlagService to check flag states.
 * ============================================
 */

/** All feature flag identifiers — must match backend FeatureFlag enum values */
export const FeatureFlag = {
  // Streaming
  ENABLE_SSE_STREAMING: "ENABLE_SSE_STREAMING",
  ENABLE_SSE_HEARTBEAT: "ENABLE_SSE_HEARTBEAT",

  // AI Agents
  ENABLE_PARALLEL_SUMMARIZATION: "ENABLE_PARALLEL_SUMMARIZATION",
  ENABLE_AGENT_TIMELINE: "ENABLE_AGENT_TIMELINE",
  ENABLE_AGENT_RETRY: "ENABLE_AGENT_RETRY",

  // Caching
  ENABLE_RESEARCH_CACHE: "ENABLE_RESEARCH_CACHE",
  ENABLE_QUERY_CACHE: "ENABLE_QUERY_CACHE",

  // Export
  ENABLE_MARKDOWN_EXPORT: "ENABLE_MARKDOWN_EXPORT",
  ENABLE_PDF_EXPORT: "ENABLE_PDF_EXPORT",

  // Observability
  ENABLE_OBSERVABILITY: "ENABLE_OBSERVABILITY",
  ENABLE_REQUEST_LOGGING: "ENABLE_REQUEST_LOGGING",
  ENABLE_SLOW_QUERY_LOG: "ENABLE_SLOW_QUERY_LOG",

  // Security
  ENABLE_RATE_LIMITING: "ENABLE_RATE_LIMITING",
  ENABLE_API_KEY_AUTH: "ENABLE_API_KEY_AUTH",
} as const;

export type FeatureFlagKey = keyof typeof FeatureFlag;
export type FeatureFlagValue = (typeof FeatureFlag)[FeatureFlagKey];
