/**
 * ============================================
 * Deep Research Platform - Axios API Client
 * ============================================
 * Typed, preconfigured Axios instance for all API calls.
 *
 * WHY Axios over fetch:
 * - Interceptor pipeline for auth, error handling, logging
 * - Automatic JSON serialization/deserialization
 * - Request/response type inference
 * - Cancellation support (AbortController compatible)
 * - Consistent timeout behavior
 * ============================================
 */

import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

import { appConfig } from "@/config/app.config";
import type { ErrorResponse } from "@/types/feature-flags";

/** Application-level API error with structured details */
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly status: number = 0,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: appConfig.apiV1Url,
    timeout: 30_000,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  // ---------- Request Interceptor ----------
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Future: inject Authorization header here
      // const token = useAuthStore.getState().token;
      // if (token) config.headers.Authorization = `Bearer ${token}`;

      // Add a client-generated request ID for tracing
      config.headers["X-Client-Request-ID"] = crypto.randomUUID();

      return config;
    },
    (error: unknown) => Promise.reject(error),
  );

  // ---------- Response Interceptor ----------
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError<ErrorResponse>) => {
      // Network error (no response from server)
      if (!error.response) {
        throw new ApiError(
          "NETWORK_ERROR",
          "Unable to reach the server. Check your connection.",
          {},
          0,
        );
      }

      const { status, data } = error.response;
      const apiError = data?.error;

      throw new ApiError(
        apiError?.code ?? "UNKNOWN_ERROR",
        apiError?.message ?? `Request failed with status ${status}`,
        apiError?.details ?? {},
        status,
      );
    },
  );

  return client;
}

/** Singleton Axios instance — use this for all API requests */
export const apiClient = createApiClient();
