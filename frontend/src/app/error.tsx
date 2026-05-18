/**
 * ============================================
 * Deep Research Platform - Global Error Boundary
 * ============================================
 * Catches unhandled errors in the React tree.
 * App Router requires error.tsx to be a Client Component.
 * ============================================
 */

"use client";

import { useEffect } from "react";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps): React.JSX.Element {
  useEffect(() => {
    // Log to error tracking service (e.g., Sentry) in future phases
    console.error("[ErrorBoundary]", error);
  }, [error]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-surface)] px-6">
      <div className="w-full max-w-md space-y-6 text-center">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-[var(--color-error)]/30 bg-[var(--color-surface-50)]">
          <span className="text-3xl">⚠️</span>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Something went wrong
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)]">
            {error.message || "An unexpected error occurred. Please try again."}
          </p>
          {error.digest && (
            <p className="text-xs text-[var(--color-text-muted)]">
              Error ID: <code>{error.digest}</code>
            </p>
          )}
        </div>

        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-brand-600)] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brand-500)]"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
