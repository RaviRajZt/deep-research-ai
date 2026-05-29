"use client";

import React, { useState, useEffect } from "react";
import { useResearchStore } from "@/store/research.store";
import { appConfig } from "@/config/app.config";

export function SessionList(): React.JSX.Element {
  const { sessions, activeSessionId, setSessions, setActiveSessionId } = useResearchStore();
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Fetch session list on mount
  useEffect(() => {
    async function fetchSessions() {
      try {
        setLoading(true);
        const res = await fetch(`${appConfig.apiV1Url}/research/session?limit=100`);
        if (res.ok) {
          const data = await res.json();
          setSessions(data.items || []);
        }
      } catch (err) {
        console.error("Failed to load historical sessions:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSessions();
  }, []);

  function handleDeleteClick(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    setDeleteConfirmId(sessionId);
  }

  async function handleConfirmDelete(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    try {
      const res = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        // Remove from local store list
        setSessions(sessions.filter((s) => s.id !== sessionId));
        // If the deleted session was active, clear it
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
        }
      } else {
        console.error("Failed to delete session");
      }
    } catch (err) {
      console.error("Error deleting session:", err);
    } finally {
      setDeleteConfirmId(null);
    }
  }

  function handleCancelDelete(e: React.MouseEvent) {
    e.stopPropagation();
    setDeleteConfirmId(null);
  }

  const filteredSessions = sessions.filter((s) =>
    s.topic.toLowerCase().includes(search.toLowerCase()),
  );

  function formatDate(dateStr: string): string {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  }

  // SSE Glowing Status bullet
  function renderStatusIcon(status: string) {
    switch (status) {
      case "completed":
        return (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </span>
        );
      case "failed":
        return (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/10 text-rose-400">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </span>
        );
      case "cancelled":
        return (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-500/10 text-slate-400">
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M18.36 18.36A9 9 0 115.64 5.64m12.72 12.72L5.64 5.64" />
            </svg>
          </span>
        );
      default: // Active states (pending, planning, researching, writing)
        return (
          <span className="relative flex h-5 w-5 items-center justify-center">
            <span className="pulse-dot absolute h-2 w-2 rounded-full bg-violet-400" />
            <span className="h-3 w-3 animate-spin rounded-full border border-violet-400 border-t-transparent" />
          </span>
        );
    }
  }

  return (
    <div className="flex h-full flex-col space-y-4">
      {/* Search Header */}
      <div className="space-y-2">
        <h2 className="font-outfit text-lg font-bold tracking-tight text-white">Research Workspace</h2>
        <p className="text-xs text-[var(--color-text-secondary)]">
          Select or launch AI research sessions below.
        </p>
      </div>

      {/* Search input with custom SVG search lens */}
      <div className="relative">
        <input
          type="text"
          placeholder="Filter research topic..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-50)] py-2.5 pl-9 pr-4 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] transition-colors focus:border-violet-500 focus:outline-none"
        />
        <svg
          className="absolute left-3 top-3 h-4 w-4 text-[var(--color-text-muted)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* History scroll list */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2">
        {loading && sessions.length === 0 ? (
          <div className="py-12 text-center text-sm text-[var(--color-text-muted)] space-y-3">
            <span className="mx-auto block h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
            <span>Loading history...</span>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--color-border)] p-6 text-center text-sm text-[var(--color-text-muted)]">
            No research sessions found.
          </div>
        ) : (
          filteredSessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const isConfirming = deleteConfirmId === session.id;
            return (
              <div
                key={session.id}
                role="button"
                tabIndex={0}
                onClick={() => !isConfirming && setActiveSessionId(session.id)}
                onKeyDown={(e) => {
                  if (!isConfirming && (e.key === "Enter" || e.key === " ")) {
                    setActiveSessionId(session.id);
                  }
                }}
                className={[
                  "glass-panel w-full rounded-xl p-3.5 text-left transition-all duration-200 focus:outline-none flex gap-3 items-start cursor-pointer group/row relative overflow-hidden",
                  isActive
                    ? "border-violet-500/40 bg-violet-500/5 shadow-md shadow-violet-950/20"
                    : "hover:bg-[var(--color-surface-100)]",
                ].join(" ")}
              >
                {/* Custom Inline Confirmation Overlay */}
                {isConfirming && (
                  <div className="absolute inset-0 z-10 flex items-center justify-between bg-slate-950/95 backdrop-blur-md px-4 py-2 border border-rose-500/20 transition-all duration-200">
                    <span className="text-xs font-semibold text-rose-200">Delete this session?</span>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => handleConfirmDelete(e, session.id)}
                        className="rounded-lg bg-rose-600 hover:bg-rose-500 px-3 py-1.5 text-[10px] text-white font-bold transition-all shadow-sm shadow-rose-950/50"
                      >
                        Delete
                      </button>
                      <button
                        onClick={(e) => handleCancelDelete(e)}
                        className="rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-[10px] text-slate-300 font-bold transition-all border border-slate-700/50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Status dot indicator */}
                <div className="mt-0.5">{renderStatusIcon(session.status)}</div>

                {/* Text details */}
                <div className="flex-1 min-w-0 space-y-1 pr-6">
                  <h3
                    className={[
                      "font-sans text-sm font-semibold truncate",
                      isActive ? "text-violet-200" : "text-[var(--color-text-primary)]",
                    ].join(" ")}
                  >
                    {session.topic}
                  </h3>
                  <div className="flex justify-between items-center text-[10px] text-[var(--color-text-muted)] font-medium">
                    <span className="uppercase tracking-widest text-violet-400/80 font-bold">
                      {session.status}
                    </span>
                    <span>{formatDate(session.created_at)}</span>
                  </div>
                </div>

                {/* Delete button (absolute position, far right) */}
                <button
                  onClick={(e) => handleDeleteClick(e, session.id)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 opacity-0 group-hover/row:opacity-100 transition-all duration-150 p-1.5 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 focus:outline-none focus:opacity-100"
                  title="Delete research workspace"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
