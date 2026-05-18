/**
 * ============================================
 * Deep Research Platform - Frontend Constants
 * ============================================
 */

/** API route path constants — keep in sync with backend API_V1_PREFIX */
export const API_ROUTES = {
  HEALTH: "/health",
  HEALTH_READY: "/health/ready",
  HEALTH_FLAGS: "/health/flags",
  // Future:
  // RESEARCH: "/research",
  // AGENTS: "/agents",
} as const;

/** UI-level constants */
export const UI = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  TOAST_DURATION_MS: 4000,
  DEBOUNCE_DELAY_MS: 300,
} as const;

/** Query cache keys for TanStack Query — centralized to avoid typos */
export const QUERY_KEYS = {
  HEALTH: ["health"] as const,
  FLAGS: ["flags"] as const,
  // Future:
  // RESEARCH_SESSIONS: ["research", "sessions"] as const,
} as const;

/** Local storage keys */
export const STORAGE_KEYS = {
  THEME: "dr:theme",
  SIDEBAR_COLLAPSED: "dr:sidebar:collapsed",
} as const;
