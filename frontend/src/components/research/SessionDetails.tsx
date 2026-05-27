"use client";

import React, { useState, useEffect } from "react";
import { useResearchStore } from "@/store/research.store";
import { useResearchStream } from "@/hooks/use-research-stream";
import { SourceInspector } from "./SourceInspector";
import { Source } from "@/types/research";
import { appConfig } from "@/config/app.config";
import { useFeatureFlags } from "@/providers/FeatureFlagProvider";
import { FeatureFlagValue } from "@/types/feature-flags";

export function SessionDetails(): React.JSX.Element {
  const { activeSessionId, resetActiveSession } = useResearchStore();
  const { activeSession, logs, connectionStatus, reconnectAttempt } = useResearchStream(activeSessionId);
  
  const [elapsedTime, setElapsedTime] = useState(0);
  const [activeTab, setActiveTab] = useState<"report" | "diagnostics">("report");
  const [copySuccess, setCopySuccess] = useState(false);

  // States for source inspector and cost telemetry
  const [sources, setSources] = useState<Source[]>([]);

  const { isEnabled } = useFeatureFlags();
  const showObservability = isEnabled("ENABLE_OBSERVABILITY" as FeatureFlagValue);

  // Fetch sources for this session
  async function fetchSources() {
    if (!activeSessionId) return;
    try {
      const res = await fetch(`${appConfig.apiV1Url}/research/session/${activeSessionId}/sources`);
      if (res.ok) {
        const data = await res.json();
        setSources(data || []);
      }
    } catch (err) {
      console.error("Failed to load sources:", err);
    }
  }

  // Fetch sources on mount / session change
  useEffect(() => {
    fetchSources();
  }, [activeSessionId]);

  // Re-fetch sources when logs change length, or session finishes
  useEffect(() => {
    fetchSources();
  }, [logs.length, activeSession?.status]);

  // Guard activeTab when flag changes
  useEffect(() => {
    if (!showObservability && activeTab === "diagnostics") {
      setActiveTab("report");
    }
  }, [showObservability, activeTab]);

  // 1. Live Elapsed Clock Timer
  useEffect(() => {
    if (!activeSession) return;
    
    const activeStates = ["pending", "planning", "researching", "writing"];
    if (!activeStates.includes(activeSession.status)) {
      // Calculate final static time
      const start = new Date(activeSession.created_at).getTime();
      const end = new Date(activeSession.updated_at).getTime();
      setElapsedTime(Math.max(Math.floor((end - start) / 1000), 0));
      return;
    }

    // Set initial elapsed
    const start = new Date(activeSession.created_at).getTime();
    setElapsedTime(Math.max(Math.floor((Date.now() - start) / 1000), 0));

    const interval = setInterval(() => {
      setElapsedTime(Math.max(Math.floor((Date.now() - start) / 1000), 0));
    }, 1000);

    return () => clearInterval(interval);
  }, [activeSession]);

  if (!activeSession) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center p-12 space-y-4">
        <span className="h-8 w-8 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
        <p className="text-sm text-[var(--color-text-muted)] font-medium">
          Retrieving live research stream and timeline metrics...
        </p>
      </div>
    );
  }

  // 2. Compute Telemetry Stats
  const totalTokens = logs.reduce((acc, log) => acc + (log.token_count || 0), 0) + (activeSession.result_token_count || 0);
  
  // Count sources discovered by checking metadata or log logs
  const discoveredSources = logs
    .filter(l => l.agent_role === "search_agent" && l.status === "completed")
    .reduce((acc, log) => acc + (((log.step_metadata as Record<string, unknown>)?.source_ids as string[] | undefined)?.length || 0), 0);

  // Compute Cost Saved from token optimization
  const sumRaw = sources.reduce((acc, s) => acc + (s.raw_token_count || 0), 0);
  const sumSummary = sources.reduce((acc, s) => acc + (s.summary_token_count || 0), 0);
  const tokensSaved = Math.max(sumRaw - sumSummary, 0);
  const costSavedDollars = (tokensSaved / 1000000) * 10.00; // $10 per 1M tokens standard

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  function handleCopy() {
    if (!activeSession?.result_summary) return;
    navigator.clipboard.writeText(activeSession.result_summary);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  }

  // Robust inline markdown parsing helper
  function parseInlineFormatting(text: string) {
    const boldRegex = /\*\*(.*?)\*\*/g;
    const codeRegex = /`(.*?)`/g;
    
    const parts = text.split(boldRegex);
    return parts.map((part, index) => {
      const isBold = index % 2 === 1;
      const subparts = part.split(codeRegex);
      
      const renderedSubparts = subparts.map((subpart, subindex) => {
        const isCode = subindex % 2 === 1;
        if (isCode) {
          return (
            <code key={subindex} className="bg-[var(--color-surface-200)] px-1.5 py-0.5 rounded text-xs font-mono text-violet-300 border border-[var(--color-border)]">
              {subpart}
            </code>
          );
        }
        return subpart;
      });

      if (isBold) {
        return <strong key={index} className="text-white font-extrabold">{renderedSubparts}</strong>;
      }
      return <span key={index}>{renderedSubparts}</span>;
    });
  }

  // Premium full markdown block renderer
  function renderMarkdown(text: string) {
    if (!text) return null;
    return text.split("\n").map((para, i) => {
      const cleanPara = para.trim();
      if (!cleanPara) return <div key={i} className="h-2" />;

      if (cleanPara.startsWith("# ")) {
        return <h1 key={i} className="text-xl font-bold font-outfit mt-5 mb-2 text-white border-b border-[var(--color-border)] pb-2">{cleanPara.substring(2)}</h1>;
      }
      if (cleanPara.startsWith("## ")) {
        return <h2 key={i} className="text-lg font-bold font-outfit mt-4 mb-2 text-white">{cleanPara.substring(3)}</h2>;
      }
      if (cleanPara.startsWith("### ")) {
        return <h3 key={i} className="text-sm font-bold font-outfit mt-3.5 mb-1.5 text-violet-200">{cleanPara.substring(4)}</h3>;
      }
      if (cleanPara.startsWith("- ") || cleanPara.startsWith("* ")) {
        return (
          <li key={i} className="ml-5 list-disc text-sm text-[var(--color-text-secondary)] mb-1 leading-relaxed">
            {parseInlineFormatting(cleanPara.substring(2))}
          </li>
        );
      }
      return (
        <p key={i} className="text-sm leading-relaxed text-[var(--color-text-secondary)] mb-2.5">
          {parseInlineFormatting(cleanPara)}
        </p>
      );
    });
  }

  // SSE Signal Badge rendering
  function renderSignalBadge() {
    switch (connectionStatus) {
      case "connected":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 pulse-dot" />
            Live Sync
          </span>
        );
      case "connecting":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-violet-500/10 px-2.5 py-1 text-xs font-bold text-violet-400 border border-violet-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
            Connecting
          </span>
        );
      case "reconnecting":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-400 border border-amber-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
            Reconnecting (Attempt {reconnectAttempt})
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-500/10 px-2.5 py-1 text-xs font-bold text-[var(--color-text-muted)] border border-slate-500/10">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
            Disconnected
          </span>
        );
    }
  }

  return (
    <div className="flex h-full flex-col space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--color-border)] pb-5">
        <div className="space-y-1.5 min-w-0">
          <button
            onClick={resetActiveSession}
            className="group flex items-center gap-1 text-xs font-bold text-[var(--color-text-muted)] hover:text-violet-400 transition-colors focus:outline-none mb-1 sm:hidden"
          >
            <svg className="h-3 w-3 transition-transform group-hover:-translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
          <h1 className="font-outfit text-xl sm:text-2xl font-extrabold tracking-tight text-white truncate pr-2">
            {activeSession.topic}
          </h1>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-md bg-[var(--color-surface-100)] border border-[var(--color-border)] px-2 py-0.5 text-3xs uppercase tracking-widest font-extrabold text-violet-400">
              {activeSession.status}
            </span>
            {renderSignalBadge()}
          </div>
        </div>

        {/* Diagnostic Panel Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("report")}
            className={[
              "rounded-lg px-3.5 py-2 text-xs font-bold transition-all focus:outline-none",
              activeTab === "report"
                ? "bg-violet-600 text-white shadow-md shadow-violet-950/20"
                : "bg-[var(--color-surface-50)] text-[var(--color-text-secondary)] hover:text-white border border-[var(--color-border)]",
            ].join(" ")}
          >
            Report Brief
          </button>
          {showObservability ? (
            <button
              onClick={() => setActiveTab("diagnostics")}
              className={[
                "rounded-lg px-3.5 py-2 text-xs font-bold transition-all focus:outline-none",
                activeTab === "diagnostics"
                  ? "bg-violet-600 text-white shadow-md shadow-violet-950/20"
                  : "bg-[var(--color-surface-50)] text-[var(--color-text-secondary)] hover:text-white border border-[var(--color-border)]",
              ].join(" ")}
            >
              Agent Timeline
            </button>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-lg bg-slate-900 border border-[var(--color-border)] px-3 py-2 text-xs text-[var(--color-text-muted)] font-bold">
              🔒 Diagnostics Locked
            </span>
          )}
        </div>
      </div>

      {/* Telemetry Cards Grid */}
      <div className="grid gap-3 grid-cols-2 sm:grid-cols-5">
        {/* Time Card */}
        <div className="glass-panel rounded-xl p-3.5 space-y-1">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            Execution Time
          </span>
          <div className="font-outfit text-base font-bold text-white flex items-baseline gap-0.5">
            {formatTime(elapsedTime)}
            <span className="text-[9px] font-medium text-[var(--color-text-muted)] ml-0.5">elapsed</span>
          </div>
        </div>

        {/* Token Card */}
        <div className="glass-panel rounded-xl p-3.5 space-y-1">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            Tokens Processed
          </span>
          <div className="font-outfit text-base font-bold text-violet-400">
            {totalTokens ? totalTokens.toLocaleString() : "0"}
          </div>
        </div>

        {/* Cost Saved Card */}
        <div className="glass-panel rounded-xl p-3.5 space-y-1">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            LLM Budget Saved
          </span>
          <div className="font-outfit text-base font-bold text-emerald-400">
            ${costSavedDollars.toFixed(2)}
          </div>
        </div>

        {/* Sources Card */}
        <div className="glass-panel rounded-xl p-3.5 space-y-1">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            Discovered Sources
          </span>
          <div className="font-outfit text-base font-bold text-white">
            {discoveredSources || "—"}
          </div>
        </div>

        {/* Active Node Card */}
        <div className="glass-panel rounded-xl p-3.5 space-y-1">
          <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            Current Operator
          </span>
          <div className="font-outfit text-xs font-bold text-violet-300 truncate">
            {activeSession.status === "completed"
              ? "Synthesis Complete"
              : activeSession.status === "failed"
              ? "Halted"
              : logs.length > 0
              ? (logs[logs.length - 1]?.agent_role || "Supervisor").replace("_", " ").toUpperCase()
              : "SUPERVISOR"}
          </div>
        </div>
      </div>

      {/* Main Tabbed Area */}
      <div className="flex-1 min-h-0 flex flex-col md:flex-row gap-6">
        {/* Left Side: Active Tab details */}
        <div className="flex-1 min-w-0 flex flex-col">
          {activeTab === "report" ? (
            <div className="flex-1 glass-panel rounded-2xl p-6 overflow-y-auto space-y-4 flex flex-col">
              {activeSession.result_summary ? (
                <>
                  <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
                    <span className="text-xs font-bold uppercase tracking-widest text-violet-400">
                      AI Synthesis Output Brief
                    </span>
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1 text-xs font-bold text-[var(--color-text-secondary)] hover:text-white transition-colors focus:outline-none"
                    >
                      {copySuccess ? (
                        <>
                          <svg className="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          Copied!
                        </>
                      ) : (
                        <>
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                          </svg>
                          Copy Report
                        </>
                      )}
                    </button>
                  </div>
                  
                  {/* Clean rendered report brief */}
                  <div className="prose flex-1 overflow-y-auto pr-1">
                    {renderMarkdown(activeSession.result_summary)}
                  </div>
                </>
              ) : activeSession.status === "failed" ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-3">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </span>
                  <div className="space-y-1">
                    <h3 className="font-outfit text-md font-bold text-white">Research Pipeline Terminated</h3>
                    <p className="text-xs text-[var(--color-text-secondary)] max-w-md">
                      {activeSession.error_message || "An unexpected agent failure halted execution."}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-4">
                  <div className="relative flex h-10 w-10 items-center justify-center">
                    <span className="pulse-dot absolute h-8 w-8 rounded-full bg-violet-500/10 border border-violet-500/30" />
                    <span className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-outfit text-sm font-bold text-white">Compiling Agent Intelligence...</h3>
                    <p className="text-xs text-[var(--color-text-secondary)]">
                      The synthesizer agent is currently collecting findings to compile the final brief.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Tab: Diagnostics / Timeline view */
            <div className="flex-1 glass-panel rounded-2xl p-6 overflow-y-auto space-y-6">
              <span className="text-xs font-bold uppercase tracking-widest text-violet-400 block border-b border-[var(--color-border)] pb-3">
                Agent Choreography & Audit Trails
              </span>

              {logs.length === 0 ? (
                <p className="text-xs text-[var(--color-text-muted)] text-center py-12">
                  Supervisor is parsing queries. Initial step logs will appear shortly...
                </p>
              ) : (
                <div className="relative border-l border-[var(--color-border)] ml-3 pl-6 space-y-6">
                  {logs.map((log) => {
                    const isRunning = log.status === "running";
                    const isFailed = log.status === "failed";

                    return (
                      <div key={log.id} className="relative group">
                        {/* Vertical connection line flow */}
                        {isRunning && (
                          <div className="absolute -left-[25px] top-4 -bottom-10 w-[2px] line-flow" />
                        )}

                        {/* Bullet step point */}
                        <span
                          className={[
                            "absolute -left-[35px] top-1 flex h-5 w-5 items-center justify-center rounded-full border text-white transition-all duration-200",
                            isRunning
                              ? "bg-violet-600 border-violet-500 shadow-md shadow-violet-500/20"
                              : isFailed
                              ? "bg-rose-500/10 border-rose-500/50 text-rose-400"
                              : "bg-[var(--color-surface-100)] border-[var(--color-border)] text-violet-400",
                          ].join(" ")}
                        >
                          {isRunning ? (
                            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-white" />
                          ) : isFailed ? (
                            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          ) : (
                            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </span>

                        {/* Step Details block */}
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                            <h4 className="font-outfit text-sm font-bold text-white flex items-center gap-2">
                              {log.agent_role.replace("_", " ").toUpperCase()}
                              {isRunning && (
                                <span className="rounded bg-violet-500/15 px-1.5 py-0.5 text-[8px] font-bold text-violet-400 uppercase tracking-widest animate-pulse">
                                  Running
                                </span>
                              )}
                            </h4>
                            <span className="text-[10px] text-[var(--color-text-muted)] font-medium">
                              {log.duration_ms ? `${(log.duration_ms / 1000).toFixed(2)}s` : ""}
                              {log.token_count ? ` • ${log.token_count.toLocaleString()} tokens` : ""}
                            </span>
                          </div>
                          
                          <p className="text-xs text-[var(--color-text-secondary)]">{log.message}</p>
                          {log.error_detail && (
                            <div className="rounded-lg bg-rose-500/5 border border-rose-500/10 p-2 text-3xs text-rose-400 font-mono">
                              {log.error_detail}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side Column: Discovered Sources Inspector */}
        <div className="w-full md:w-80 shrink-0 glass-panel rounded-2xl p-5 flex flex-col h-[400px] md:h-auto overflow-hidden">
          <SourceInspector sessionId={activeSessionId!} activeLogs={logs} />
        </div>
      </div>
    </div>
  );
}
