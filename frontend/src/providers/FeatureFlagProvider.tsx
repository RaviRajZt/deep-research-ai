/**
 * ============================================
 * Deep Research Platform - Feature Flag Provider
 * ============================================
 * Loads server-side feature flags and exposes them
 * throughout the component tree via React context.
 *
 * Usage:
 *   const { isEnabled } = useFeatureFlags();
 *   if (isEnabled("ENABLE_SSE_STREAMING")) { ... }
 * ============================================
 */

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { featureFlagService } from "@/config/feature-flags";
import type { FeatureFlagValue } from "@/types/feature-flags";

interface FeatureFlagContextValue {
  isEnabled: (flag: FeatureFlagValue) => boolean;
  getAllFlags: () => Record<string, boolean>;
  isLoading: boolean;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | null>(null);

export function FeatureFlagProvider({ children }: { children: ReactNode }): React.JSX.Element {
  const [isLoading, setIsLoading] = useState(true);
  const [, forceRender] = useState(0);

  useEffect(() => {
    featureFlagService
      .loadFromServer()
      .then(() => forceRender((n) => n + 1))
      .finally(() => setIsLoading(false));
  }, []);

  const value: FeatureFlagContextValue = {
    isEnabled: (flag) => featureFlagService.isEnabled(flag),
    getAllFlags: () => featureFlagService.getAllFlags(),
    isLoading,
  };

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlags(): FeatureFlagContextValue {
  const ctx = useContext(FeatureFlagContext);
  if (!ctx) {
    throw new Error("useFeatureFlags must be used within a FeatureFlagProvider");
  }
  return ctx;
}
