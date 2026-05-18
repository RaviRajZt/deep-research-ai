/**
 * ============================================
 * Deep Research Platform - 404 Not Found
 * ============================================
 */

import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "404 — Page Not Found",
};

export default function NotFoundPage(): React.JSX.Element {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-surface)] px-6">
      <div className="w-full max-w-md space-y-6 text-center">
        <p className="text-8xl font-bold text-[var(--color-surface-200)]">404</p>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Page not found
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)]">
            The page you are looking for does not exist or has been moved.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-50)] px-5 py-2.5 text-sm font-medium text-[var(--color-text-primary)] transition-colors hover:border-[var(--color-border-hover)] hover:bg-[var(--color-surface-100)]"
        >
          ← Back to Dashboard
        </Link>
      </div>
    </main>
  );
}
