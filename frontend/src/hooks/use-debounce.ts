/**
 * ============================================
 * Deep Research Platform - useDebounce Hook
 * ============================================
 * Debounces a value by the given delay.
 * Used for search inputs to avoid excessive API calls.
 * ============================================
 */

"use client";

import { useEffect, useState } from "react";

import { UI } from "@/config/constants";

export function useDebounce<T>(value: T, delay: number = UI.DEBOUNCE_DELAY_MS): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
