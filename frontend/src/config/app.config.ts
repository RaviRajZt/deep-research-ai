/**
 * ============================================
 * Deep Research Platform - Frontend Environment Config
 * ============================================
 * Centralizes all environment variable access.
 *
 * WHY a config module instead of direct process.env access:
 * - Single place to validate env vars at startup
 * - Typed access with defaults
 * - Prevents scattered process.env calls across the codebase
 * - Easy to mock in tests
 * ============================================
 */


function optionalEnv(key: string, defaultValue: string): string {
  return process.env[key] ?? defaultValue;
}

function boolEnv(key: string, defaultValue: boolean): boolean {
  const value = process.env[key];
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === "true" || value === "1";
}

/** Validated, typed frontend configuration */
export const appConfig = {
  // ---------- API ----------
  apiBaseUrl: optionalEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000"),
  apiV1Prefix: "/api/v1",

  // ---------- App ----------
  appEnv: optionalEnv("NEXT_PUBLIC_APP_ENV", "development"),
  appVersion: optionalEnv("NEXT_PUBLIC_APP_VERSION", "0.0.0"),
  appName: "Deep Research",

  // ---------- Feature Flags ----------
  enableSSE: boolEnv("NEXT_PUBLIC_ENABLE_SSE", false),
  enableObservability: boolEnv("NEXT_PUBLIC_ENABLE_OBSERVABILITY", false),

  // ---------- Computed ----------
  get apiV1Url(): string {
    return `${this.apiBaseUrl}${this.apiV1Prefix}`;
  },
  get isDevelopment(): boolean {
    return this.appEnv === "development";
  },
  get isProduction(): boolean {
    return this.appEnv === "production";
  },
} as const;

export type AppConfig = typeof appConfig;
