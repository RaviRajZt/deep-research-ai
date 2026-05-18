/**
 * ============================================
 * Deep Research Platform - Homepage
 * ============================================
 * Platform landing/dashboard page.
 * Phase 1: Shows platform status and health.
 * Future phases: Research session management.
 * ============================================
 */

import type { Metadata } from "next";

import { HealthStatus } from "@/components/health/HealthStatus";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Deep Research Platform — AI-powered multi-agent research dashboard.",
};

export default function HomePage(): React.JSX.Element {
  return (
    <main className="min-h-screen bg-[var(--color-surface)] px-6 py-12">
      <div className="mx-auto max-w-4xl space-y-10">
        {/* ---------- Header ---------- */}
        <header className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-50)] px-3 py-1 text-xs font-medium text-[var(--color-text-secondary)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-brand-500)]" />
            Phase 1 Foundation
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)]">
            Deep Research{" "}
            <span className="bg-gradient-to-r from-[var(--color-brand-400)] to-[var(--color-brand-600)] bg-clip-text text-transparent">
              Platform
            </span>
          </h1>
          <p className="text-lg text-[var(--color-text-secondary)]">
            Enterprise AI Research Agent Platform — multi-agent orchestration with real-time
            streaming.
          </p>
        </header>

        {/* ---------- Platform Health ---------- */}
        <section aria-labelledby="health-heading">
          <h2
            id="health-heading"
            className="mb-4 text-sm font-semibold uppercase tracking-widest text-[var(--color-text-muted)]"
          >
            Platform Status
          </h2>
          <HealthStatus />
        </section>

        {/* ---------- Phase Roadmap ---------- */}
        <section aria-labelledby="roadmap-heading">
          <h2
            id="roadmap-heading"
            className="mb-4 text-sm font-semibold uppercase tracking-widest text-[var(--color-text-muted)]"
          >
            Roadmap
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {PHASES.map((phase) => (
              <PhaseCard key={phase.phase} {...phase} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

const PHASES = [
  {
    phase: "Phase 1",
    title: "Foundation",
    description: "Monorepo, FastAPI, Next.js, PostgreSQL, Redis, Feature Flags",
    status: "current" as const,
  },
  {
    phase: "Phase 2",
    title: "Agent Orchestration",
    description: "LangGraph multi-agent pipeline, token-safe processing",
    status: "upcoming" as const,
  },
  {
    phase: "Phase 3",
    title: "Live Streaming",
    description: "SSE real-time research updates, agent timeline visualization",
    status: "upcoming" as const,
  },
  {
    phase: "Phase 4",
    title: "Observability",
    description: "OpenTelemetry, distributed tracing, analytics dashboard",
    status: "upcoming" as const,
  },
];

interface PhaseCardProps {
  phase: string;
  title: string;
  description: string;
  status: "current" | "upcoming";
}

function PhaseCard({ phase, title, description, status }: PhaseCardProps): React.JSX.Element {
  return (
    <div
      className={[
        "rounded-xl border p-4 transition-colors duration-200",
        status === "current"
          ? "border-[var(--color-brand-600)] bg-[var(--color-surface-50)]"
          : "border-[var(--color-border)] bg-[var(--color-surface-50)] opacity-60",
      ].join(" ")}
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-[var(--color-text-muted)]">
          {phase}
        </span>
        {status === "current" && (
          <span className="rounded-full bg-[var(--color-brand-500)] px-2 py-0.5 text-xs font-medium text-white">
            Active
          </span>
        )}
      </div>
      <h3 className="font-semibold text-[var(--color-text-primary)]">{title}</h3>
      <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{description}</p>
    </div>
  );
}
