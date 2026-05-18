/**
 * ============================================
 * Deep Research Platform - Utility Functions
 * ============================================
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS class names safely, resolving conflicts.
 * The standard utility used across all components.
 *
 * Usage:
 *   cn("px-4 py-2", isActive && "bg-brand-500", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string to a locale-aware readable format.
 */
export function formatDate(dateStr: string, locale = "en-US"): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateStr));
}

/**
 * Truncate a string to a max length with ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + "...";
}

/**
 * Sleep for a given number of milliseconds.
 * Useful in retry logic and SSE reconnection delays.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Type-safe object entries (preserves key types).
 */
export function typedEntries<T extends Record<string, unknown>>(
  obj: T,
): [keyof T, T[keyof T]][] {
  return Object.entries(obj) as [keyof T, T[keyof T]][];
}
