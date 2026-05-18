/**
 * ============================================
 * Deep Research Platform - Zustand App Store
 * ============================================
 * Global UI state management.
 *
 * WHY Zustand over Redux:
 * - Minimal boilerplate — no actions, reducers, selectors ceremony
 * - First-class TypeScript support
 * - React 18 concurrent mode compatible
 * - Supports middleware (devtools, persist, immer)
 *
 * Architecture rules:
 * - Stores hold UI state ONLY (not server state — that's TanStack Query)
 * - One store per concern domain
 * - Selectors are memoized via useShallow when needed
 * ============================================
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";

export type Theme = "dark" | "light" | "system";

interface AppState {
  // ---------- State ----------
  theme: Theme;
  sidebarCollapsed: boolean;
  globalLoading: boolean;

  // ---------- Actions ----------
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setGlobalLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Defaults
      theme: "dark",
      sidebarCollapsed: false,
      globalLoading: false,

      // Actions
      setTheme: (theme) => set({ theme }, false, "setTheme"),

      toggleSidebar: () =>
        set(
          (state) => ({ sidebarCollapsed: !state.sidebarCollapsed }),
          false,
          "toggleSidebar",
        ),

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }, false, "setSidebarCollapsed"),

      setGlobalLoading: (globalLoading) =>
        set({ globalLoading }, false, "setGlobalLoading"),
    }),
    { name: "AppStore" },
  ),
);
