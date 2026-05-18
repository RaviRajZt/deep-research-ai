/**
 * ============================================
 * Deep Research Platform - Root Providers
 * ============================================
 * Composes all providers in the correct dependency order.
 *
 * Order matters:
 * 1. QueryProvider — must wrap everything that uses TanStack Query
 * 2. FeatureFlagProvider — may use QueryClient internally in future
 *
 * Adding a new provider: add it here, not in layout.tsx.
 * This keeps layout.tsx clean and providers composable.
 * ============================================
 */

"use client";

import type { ReactNode } from "react";

import { FeatureFlagProvider } from "./FeatureFlagProvider";
import { QueryProvider } from "./QueryProvider";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps): React.JSX.Element {
  return (
    <QueryProvider>
      <FeatureFlagProvider>{children}</FeatureFlagProvider>
    </QueryProvider>
  );
}
