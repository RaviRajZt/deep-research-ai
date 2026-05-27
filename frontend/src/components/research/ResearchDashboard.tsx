"use client";

import React from "react";
import { useResearchStore } from "@/store/research.store";
import { SessionList } from "./SessionList";
import { CreateSessionForm } from "./CreateSessionForm";
import { SessionDetails } from "./SessionDetails";

export function ResearchDashboard(): React.JSX.Element {
  const { activeSessionId } = useResearchStore();

  return (
    <div className="w-full">
      {!activeSessionId ? (
        /* Landing Dashboard View */
        <div className="grid gap-8 lg:grid-cols-12 items-start">
          {/* Left Side: Create Session Form */}
          <div className="lg:col-span-7 space-y-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/5 px-3 py-1 text-xs font-semibold text-violet-400">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-400 pulse-dot" />
                Phase 6 Production Streaming Ready
              </div>
              <h1 className="font-outfit text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
                Deep Research{" "}
                <span className="bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent">
                  Dashboard
                </span>
              </h1>
              <p className="text-sm text-[var(--color-text-secondary)] max-w-xl">
                Deploy orchestrated AI research pipelines to scrape multi-source webs, isolate semantic chunks, and aggregate insights with strict context-safe budgeting.
              </p>
            </div>

            <CreateSessionForm />
          </div>

          {/* Right Side: Session History List */}
          <div className="lg:col-span-5 h-[580px] glass-panel rounded-2xl p-5 flex flex-col">
            <SessionList />
          </div>
        </div>
      ) : (
        /* Active Investigation Splitscreen View */
        <div className="grid gap-6 lg:grid-cols-12 h-[calc(100vh-140px)] min-h-[500px]">
          {/* History Sidebar - hidden on mobile, visible on lg */}
          <div className="hidden lg:col-span-3 glass-panel rounded-2xl p-5 flex flex-col h-full">
            <SessionList />
          </div>

          {/* Active Workspace */}
          <div className="lg:col-span-9 h-full flex flex-col">
            <SessionDetails />
          </div>
        </div>
      )}
    </div>
  );
}
