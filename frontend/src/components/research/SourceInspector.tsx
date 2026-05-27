"use client";

import React, { useState, useEffect } from "react";
import { Source, ExecutionLog } from "@/types/research";
import { appConfig } from "@/config/app.config";

interface SourceInspectorProps {
  sessionId: string;
  activeLogs: ExecutionLog[];
}

export function SourceInspector({ sessionId, activeLogs }: SourceInspectorProps): React.JSX.Element {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);

  // 1. Fetch Sources
  async function fetchSources() {
    if (!sessionId) return;
    try {
      setLoading(true);
      const res = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}/sources`);
      if (res.ok) {
        const data = await res.json();
        setSources(data || []);
      }
    } catch (err) {
      console.error("Failed to load sources in inspector:", err);
    } finally {
      setLoading(false);
    }
  }

  // Fetch on mount / sessionId change
  useEffect(() => {
    fetchSources();
  }, [sessionId]);

  // Re-fetch when active logs complete or update (re-fetching sources in real-time)
  useEffect(() => {
    // Re-fetch on major changes
    fetchSources();
  }, [activeLogs.length]);

  // Render Status Badge
  function renderStatusBadge(status: string) {
    switch (status) {
      case "fetched":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[9px] font-bold text-emerald-400 border border-emerald-500/20">
            <span className="h-1 w-1 rounded-full bg-emerald-400" />
            Fetched
          </span>
        );
      case "fetching":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-violet-500/10 px-2 py-0.5 text-[9px] font-bold text-violet-400 border border-violet-500/20 animate-pulse">
            <span className="h-1 w-1 rounded-full bg-violet-400 animate-ping" />
            Scraping
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-[9px] font-bold text-rose-400 border border-rose-500/20">
            <span className="h-1 w-1 rounded-full bg-rose-400" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-500/10 px-2 py-0.5 text-[9px] font-bold text-[var(--color-text-muted)] border border-slate-500/10">
            <span className="h-1 w-1 rounded-full bg-slate-500" />
            Pending
          </span>
        );
    }
  }

  // Helper to parse simple markdown in summary
  function renderMarkdown(text: string) {
    if (!text) return null;
    return text.split("\n").map((para, i) => {
      const cleanPara = para.trim();
      if (!cleanPara) return <div key={i} className="h-2" />;

      if (cleanPara.startsWith("# ")) {
        return <h1 key={i} className="text-base font-bold font-outfit mt-3 mb-1 text-white">{cleanPara.substring(2)}</h1>;
      }
      if (cleanPara.startsWith("## ")) {
        return <h2 key={i} className="text-sm font-bold font-outfit mt-3 mb-1 text-white">{cleanPara.substring(3)}</h2>;
      }
      if (cleanPara.startsWith("### ")) {
        return <h3 key={i} className="text-xs font-bold font-outfit mt-2 mb-1 text-violet-200">{cleanPara.substring(4)}</h3>;
      }
      if (cleanPara.startsWith("- ") || cleanPara.startsWith("* ")) {
        return <li key={i} className="ml-3 list-disc text-xs text-[var(--color-text-secondary)] mb-0.5">{cleanPara.substring(2)}</li>;
      }

      // Check for inline bold (**text**)
      const boldRegex = /\*\*(.*?)\*\*/g;
      if (boldRegex.test(cleanPara)) {
        const parts = cleanPara.split(boldRegex);
        return (
          <p key={i} className="text-xs leading-relaxed text-[var(--color-text-secondary)] mb-2">
            {parts.map((part, index) => index % 2 === 1 ? <strong key={index} className="text-white font-semibold">{part}</strong> : part)}
          </p>
        );
      }

      return <p key={i} className="text-xs leading-relaxed text-[var(--color-text-secondary)] mb-2">{cleanPara}</p>;
    });
  }

  return (
    <div className="flex h-full flex-col space-y-4">
      <div className="flex justify-between items-center border-b border-[var(--color-border)] pb-3">
        <div className="space-y-0.5">
          <h3 className="font-outfit text-sm font-extrabold text-white flex items-center gap-1.5">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-violet-500/10 text-violet-400">
              🔗
            </span>
            Source Inspector
          </h3>
          <p className="text-[10px] text-[var(--color-text-muted)] font-medium">
            Analyze discovered sites and metrics
          </p>
        </div>
        <span className="rounded-full bg-[var(--color-surface-100)] border border-[var(--color-border)] px-2 py-0.5 text-[10px] font-bold text-violet-400">
          {sources.length} total
        </span>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {loading && sources.length === 0 ? (
          <div className="py-8 text-center text-xs text-[var(--color-text-muted)] space-y-2">
            <span className="mx-auto block h-4 w-4 animate-spin rounded-full border border-violet-500 border-t-transparent" />
            <span>Parsing domains...</span>
          </div>
        ) : sources.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--color-border)] p-8 text-center text-xs text-[var(--color-text-muted)]">
            No sources discovered yet. Discovery starts during the Search Agent phase.
          </div>
        ) : (
          sources.map((source) => {
            const hasSummary = !!source.source_metadata?.summary_text;
            return (
              <button
                key={source.id}
                onClick={() => setSelectedSource(source)}
                className="w-full text-left glass-panel hover:bg-[var(--color-surface-100)] border-[var(--color-border)] rounded-xl p-3 flex flex-col gap-2 transition-all duration-200 focus:outline-none relative group overflow-hidden"
              >
                {/* Visual hover indicator */}
                <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-violet-500 scale-y-0 group-hover:scale-y-100 transition-transform origin-top duration-200" />
                
                <div className="flex justify-between items-start gap-2 w-full">
                  <div className="min-w-0 flex-1">
                    <span className="text-[9px] font-bold uppercase tracking-widest text-violet-400 block mb-0.5 truncate">
                      {source.domain || "Unknown Domain"}
                    </span>
                    <h4 className="font-sans text-xs font-bold text-white truncate max-w-full">
                      {source.title || source.url}
                    </h4>
                  </div>
                  <div className="shrink-0">{renderStatusBadge(source.fetch_status)}</div>
                </div>

                <div className="flex justify-between items-center text-[10px] text-[var(--color-text-muted)] font-medium border-t border-[var(--color-border)] pt-2 mt-1">
                  <span>
                    {source.chunk_count ? `${source.chunk_count} chunks` : "no chunks"}
                  </span>
                  {hasSummary ? (
                    <span className="text-violet-400 font-bold group-hover:text-violet-300 transition-colors flex items-center gap-0.5">
                      View Summary
                      <svg className="h-3 w-3 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                      </svg>
                    </span>
                  ) : source.fetch_error ? (
                    <span className="text-rose-400 font-bold max-w-[120px] truncate">{source.fetch_error}</span>
                  ) : (
                    <span>Pending summary</span>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Slide-over Detail Modal */}
      {selectedSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="glass-panel glowing-active rounded-2xl max-w-xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl p-6 relative">
            
            {/* Close Button */}
            <button
              onClick={() => setSelectedSource(null)}
              className="absolute top-4 right-4 flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--color-surface-100)] border border-[var(--color-border)] hover:border-violet-500/40 text-[var(--color-text-secondary)] hover:text-white transition-all focus:outline-none"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Header info */}
            <div className="space-y-1.5 border-b border-[var(--color-border)] pb-4 mb-4 pr-8">
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-violet-400">
                {selectedSource.domain} • Detailed Source Analysis
              </span>
              <h3 className="font-outfit text-base font-extrabold text-white leading-tight">
                {selectedSource.title || "Untitled Document"}
              </h3>
              <a
                href={selectedSource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[10px] font-bold text-violet-400 hover:text-violet-300 transition-colors"
              >
                Open Scraped Link
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-2.5 bg-[var(--color-surface-50)] border border-[var(--color-border)] rounded-xl p-3.5 mb-4 text-center">
              <div>
                <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] block mb-0.5">
                  Raw Tokens
                </span>
                <span className="font-outfit text-sm font-bold text-white">
                  {selectedSource.raw_token_count ? selectedSource.raw_token_count.toLocaleString() : "—"}
                </span>
              </div>
              <div>
                <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] block mb-0.5">
                  Summary Tokens
                </span>
                <span className="font-outfit text-sm font-bold text-violet-400">
                  {selectedSource.summary_token_count ? selectedSource.summary_token_count.toLocaleString() : "—"}
                </span>
              </div>
              <div>
                <span className="text-[9px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] block mb-0.5">
                  Token Savings
                </span>
                <span className="font-outfit text-sm font-bold text-emerald-400 block">
                  {selectedSource.raw_token_count && selectedSource.summary_token_count
                    ? `${(100 - (selectedSource.summary_token_count / selectedSource.raw_token_count) * 100).toFixed(0)}%`
                    : "—"}
                </span>
              </div>
            </div>

            {/* AI Summary Scroll Box */}
            <div className="flex-1 overflow-y-auto pr-1">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-violet-400 mb-2 border-b border-[var(--color-border)] pb-1.5">
                AI Source Summary
              </h4>
              {selectedSource.source_metadata?.summary_text ? (
                <div className="prose">
                  {renderMarkdown(selectedSource.source_metadata.summary_text as string)}
                </div>
              ) : selectedSource.fetch_status === "failed" ? (
                <div className="rounded-lg bg-rose-500/5 border border-rose-500/10 p-4 text-center space-y-2">
                  <span className="text-xs font-bold text-rose-400 block">Scrape Failure Details</span>
                  <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                    {selectedSource.fetch_error || "Scraper timed out or received an invalid status code during network request."}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-[var(--color-text-muted)] italic text-center py-8">
                  The Summarizer Agent is currently executing parallel token-safe chunk analysis. Summary will render in real time.
                </p>
              )}
            </div>

            {/* Footer close */}
            <div className="border-t border-[var(--color-border)] pt-4 mt-4 flex justify-end">
              <button
                onClick={() => setSelectedSource(null)}
                className="rounded-lg bg-violet-600 hover:bg-violet-500 px-4 py-2 text-xs font-bold text-white transition-all shadow-md shadow-violet-950/20 focus:outline-none"
              >
                Close Analysis
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
