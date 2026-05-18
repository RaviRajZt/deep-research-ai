/**
 * ============================================
 * Deep Research Platform - useHealth Hook
 * ============================================
 * TanStack Query hook for health check data.
 *
 * Separating the query hook from the API function:
 * - API function is pure and testable without React
 * - Hook handles loading, error, and refetch state
 * - Consistent caching via QUERY_KEYS constants
 * ============================================
 */

"use client";

import { useQuery } from "@tanstack/react-query";

import { QUERY_KEYS } from "@/config/constants";
import { fetchHealth, fetchFeatureFlags } from "@/lib/api/health";
import type { HealthCheckResponse } from "@/types/feature-flags";

export function useHealth() {
  return useQuery<HealthCheckResponse>({
    queryKey: QUERY_KEYS.HEALTH,
    queryFn: fetchHealth,
    // Refetch health every 30 seconds to detect degraded state
    refetchInterval: 30_000,
    // Don't throw on error — health endpoint returning 503 is expected
    throwOnError: false,
  });
}

export function useFeatureFlagsQuery() {
  return useQuery<Record<string, boolean>>({
    queryKey: QUERY_KEYS.FLAGS,
    queryFn: fetchFeatureFlags,
    staleTime: 60_000,   // Flags don't change often
    retry: 1,
    throwOnError: false,
  });
}
