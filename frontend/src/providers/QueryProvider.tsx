/**
 * ============================================
 * Deep Research Platform - TanStack Query Provider
 * ============================================
 * Sets up the QueryClient with production-grade defaults.
 *
 * WHY centralized QueryClient config:
 * - Consistent retry, stale time, and error handling globally
 * - DevTools only loaded in development (zero production overhead)
 * - Single place to tune caching strategy
 * ============================================
 */

"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { appConfig } from "@/config/app.config";

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Data considered fresh for 30 seconds — avoids redundant refetches
        staleTime: 30_000,
        // Keep unused cache for 5 minutes
        gcTime: 5 * 60_000,
        // Retry failed queries up to 2 times with exponential backoff
        retry: 2,
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
        // Refetch on window focus in production only
        refetchOnWindowFocus: appConfig.isProduction,
      },
      mutations: {
        // Do not retry mutations by default — side effects may not be idempotent
        retry: 0,
      },
    },
  });
}

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps): React.JSX.Element {
  // Create QueryClient once per component lifecycle
  // (useState prevents re-creation on re-renders)
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {appConfig.isDevelopment && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom" />
      )}
    </QueryClientProvider>
  );
}
