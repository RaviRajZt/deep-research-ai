/**
 * ============================================
 * Deep Research Platform - Loading UI
 * ============================================
 * App Router streaming loading skeleton.
 * Shown while page segments are loading.
 * ============================================
 */

export default function Loading(): React.JSX.Element {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-surface)]">
      <div className="flex flex-col items-center gap-4">
        {/* Animated brand spinner */}
        <div className="relative h-12 w-12">
          <div className="absolute inset-0 rounded-full border-2 border-[var(--color-surface-200)]" />
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-[var(--color-brand-500)]" />
        </div>
        <p className="text-sm text-[var(--color-text-muted)]">Loading…</p>
      </div>
    </main>
  );
}
