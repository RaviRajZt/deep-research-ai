/**
 * ============================================
 * Deep Research Platform - Health API Module
 * ============================================
 * Typed API functions for health endpoints.
 *
 * Pattern: API modules export plain async functions.
 * React hooks (in /hooks) wrap these with TanStack Query.
 * This separation makes the API layer testable without React.
 * ============================================
 */

import { apiClient } from "@/lib/api-client";
import type { HealthCheckResponse, ReadinessResponse } from "@/types/feature-flags";

export async function fetchHealth(): Promise<HealthCheckResponse> {
  const { data } = await apiClient.get<HealthCheckResponse>("/health");
  return data;
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const { data } = await apiClient.get<ReadinessResponse>("/health/ready");
  return data;
}

export async function fetchFeatureFlags(): Promise<Record<string, boolean>> {
  const { data } = await apiClient.get<{ environment: string; flags: Record<string, boolean> }>(
    "/health/flags",
  );
  return data.flags;
}
