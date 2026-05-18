/**
 * ============================================
 * Deep Research Platform - Frontend Feature Flags
 * ============================================
 * Client-side feature flag service.
 *
 * Two sources (priority order):
 * 1. Server-fetched flags from GET /api/v1/health/flags
 *    (reflects backend runtime state, DB-driven in future)
 * 2. NEXT_PUBLIC_* env vars (build-time defaults)
 *
 * WHY this two-source approach:
 * - Env vars give instant defaults with zero latency
 * - Server flags enable runtime control without redeployment
 * - Graceful fallback if server is unavailable
 * ============================================
 */

import { appConfig } from "@/config/app.config";
import type { FeatureFlagValue } from "@/types/feature-flags";

/** Build-time flag defaults from environment variables */
const ENV_FLAG_DEFAULTS: Record<string, boolean> = {
  ENABLE_SSE_STREAMING: appConfig.enableSSE,
  ENABLE_OBSERVABILITY: appConfig.enableObservability,
};

export class FeatureFlagService {
  private serverFlags: Record<string, boolean> = {};
  private initialized = false;

  /**
   * Load flag state from the backend API.
   * Should be called during app initialization (in a Provider).
   * Fails gracefully — falls back to env defaults.
   */
  async loadFromServer(): Promise<void> {
    if (appConfig.isProduction) {
      // Flags endpoint is restricted in production
      this.initialized = true;
      return;
    }

    try {
      const res = await fetch(`${appConfig.apiV1Url}/health/flags`, {
        next: { revalidate: 60 }, // ISR: re-fetch every 60 seconds
      });
      if (res.ok) {
        const data = (await res.json()) as { flags: Record<string, boolean> };
        this.serverFlags = data.flags;
      }
    } catch {
      // Silently fall back to env defaults — non-critical
    } finally {
      this.initialized = true;
    }
  }

  /**
   * Check if a feature flag is enabled.
   *
   * Priority:
   * 1. Server-fetched flag (runtime)
   * 2. Environment variable default (build-time)
   * 3. Global default: false
   */
  isEnabled(flag: FeatureFlagValue): boolean {
    if (flag in this.serverFlags) {
      return this.serverFlags[flag] ?? false;
    }
    return ENV_FLAG_DEFAULTS[flag] ?? false;
  }

  getAllFlags(): Record<string, boolean> {
    return { ...ENV_FLAG_DEFAULTS, ...this.serverFlags };
  }
}

/** Singleton instance for use outside React (in API client, utilities, etc.) */
export const featureFlagService = new FeatureFlagService();
