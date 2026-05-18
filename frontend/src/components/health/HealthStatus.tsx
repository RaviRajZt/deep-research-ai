/**
 * ============================================
 * Deep Research Platform - HealthStatus Component
 * ============================================
 * Displays real-time platform health from the backend API.
 * Uses the useHealth hook with TanStack Query polling.
 * ============================================
 */

"use client";

import React from "react";

import { useHealth } from "@/hooks/use-health";
import type { HealthStatus, ServiceHealth } from "@/types/feature-flags";
import { cn } from "@/lib/utils";

export function HealthStatus(): React.JSX.Element {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-50)] p-6">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 animate-pulse rounded-full bg-[var(--color-brand-500)]" />
          <span className="text-sm text-[var(--color-text-secondary)]">
            Checking platform status...
          </span>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl border border-[var(--color-error)]/30 bg-[var(--color-surface-50)] p-6">
        <div className="flex items-center gap-3">
          <StatusDot status="unhealthy" />
          <span className="text-sm font-medium text-[var(--color-text-primary)]">
            Unable to reach backend
          </span>
          <span className="ml-auto text-xs text-[var(--color-text-muted)]">
            Retrying automatically…
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-50)] p-6 space-y-4">
      {/* Overall status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusDot status={data.status} />
          <span className="font-medium capitalize text-[var(--color-text-primary)]">
            {data.status}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
          <span>v{data.version}</span>
          <span className="rounded-full border border-[var(--color-border)] px-2 py-0.5 capitalize">
            {data.environment}
          </span>
        </div>
      </div>

      {/* Service breakdown */}
      {data.services.length > 0 && (
        <div className="space-y-2 border-t border-[var(--color-border)] pt-4">
          {data.services.map((service) => (
            <ServiceRow key={service.name} service={service} />
          ))}
        </div>
      )}
    </div>
  );
}

function ServiceRow({ service }: { service: ServiceHealth }): React.JSX.Element {
  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center gap-2">
        <StatusDot status={service.status} size="sm" />
        <span className="capitalize text-[var(--color-text-secondary)]">{service.name}</span>
      </div>
      <div className="flex items-center gap-3">
        {service.latency_ms !== null && (
          <span className="text-xs text-[var(--color-text-muted)]">
            {service.latency_ms}ms
          </span>
        )}
        {service.error && (
          <span className="max-w-[200px] truncate text-xs text-[var(--color-error)]">
            {service.error}
          </span>
        )}
      </div>
    </div>
  );
}

interface StatusDotProps {
  /** Narrowed to the HealthStatus union — prevents passing arbitrary strings */
  status: HealthStatus;
  size?: "sm" | "md";
}

function StatusDot({ status, size = "md" }: StatusDotProps): React.JSX.Element {
  return (
    <span
      className={cn(
        "rounded-full flex-shrink-0",
        size === "sm" ? "h-1.5 w-1.5" : "h-2 w-2",
        {
          "bg-[var(--color-success)] animate-pulse-slow": status === "healthy",
          "bg-[var(--color-error)]": status === "unhealthy",
          "bg-[var(--color-warning)]": status === "degraded",
        },
      )}
    />
  );
}
