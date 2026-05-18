/**
 * ============================================
 * Deep Research Platform - Shared API Contracts
 * ============================================
 * TypeScript interfaces that mirror backend Pydantic schemas.
 *
 * WHY shared contracts:
 * - Single source of truth for API shapes
 * - Type errors caught at compile time, not runtime
 * - Auto-complete in IDE for API responses
 * - Easy to version (contracts/v1/, contracts/v2/)
 *
 * IMPORTANT: Keep in sync with backend app/schemas/*.py
 * ============================================
 */

// ---------- Common ----------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface SuccessResponse {
  success: boolean;
  message: string;
}

// ---------- Health ----------

export type HealthStatus = "healthy" | "unhealthy" | "degraded";

export interface ServiceHealth {
  name: string;
  status: HealthStatus;
  latency_ms: number | null;
  error: string | null;
}

export interface HealthCheckResponse {
  status: HealthStatus;
  version: string;
  environment: string;
  services: ServiceHealth[];
}

export interface ReadinessResponse {
  ready: boolean;
  checks: Record<string, boolean>;
}

export interface FeatureFlagResponse {
  environment: string;
  flags: Record<string, boolean>;
}

// ---------- Research (future phase stubs) ----------

export type ResearchStatus =
  | "pending"
  | "planning"
  | "researching"
  | "writing"
  | "reviewing"
  | "completed"
  | "failed"
  | "cancelled";

export interface ResearchSession {
  id: string;
  query: string;
  status: ResearchStatus;
  created_at: string;
  updated_at: string;
}

// ---------- SSE Events (future phase stubs) ----------

export type SSEEventType =
  | "agent_start"
  | "agent_progress"
  | "agent_complete"
  | "agent_error"
  | "research_update"
  | "heartbeat";

export interface SSEEvent<T = unknown> {
  event: SSEEventType;
  data: T;
  id?: string;
}
