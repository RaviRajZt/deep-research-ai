import type { Metadata } from "next";
import { ResearchDashboard } from "@/components/research/ResearchDashboard";
import { HealthStatus } from "@/components/health/HealthStatus";

export const metadata: Metadata = {
  title: "AI Deep Research Engine — Console Dashboard",
  description: "Enterprise multi-agent research orchestration console with real-time SSE streaming.",
};

export default function HomePage(): React.JSX.Element {
  return (
    <main className="min-h-screen bg-[var(--color-surface)] px-4 py-8 md:px-8 md:py-12">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* ---------- Top Telemetry Console Bar ---------- */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-[var(--color-surface-50)] border border-[var(--color-border)] rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600 shadow-md shadow-violet-950/20 text-white font-extrabold text-lg">
              Ω
            </span>
            <div>
              <h2 className="font-outfit text-sm font-extrabold text-white tracking-tight leading-none">
                Deep Research Console
              </h2>
              <span className="text-[10px] text-[var(--color-text-muted)] font-medium">
                v0.6.0 • Enterprise Core
              </span>
            </div>
          </div>

          {/* Micro health indicator tag */}
          <div className="flex items-center gap-4">
            <HealthStatus />
          </div>
        </div>

        {/* ---------- Main Orchestrated Dashboard ---------- */}
        <section aria-label="Research Dashboard Application">
          <ResearchDashboard />
        </section>
      </div>
    </main>
  );
}
