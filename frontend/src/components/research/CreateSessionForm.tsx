"use client";

import React, { useState } from "react";
import { useResearchStore } from "@/store/research.store";
import { appConfig } from "@/config/app.config";
import { ResearchSession } from "@/types/research";
import { useFeatureFlags } from "@/providers/FeatureFlagProvider";
import { FeatureFlagValue } from "@/types/feature-flags";

export function CreateSessionForm(): React.JSX.Element {
  const { addSession, setActiveSessionId } = useResearchStore();
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [concurrency, setConcurrency] = useState(3);
  const [maxSources, setMaxSources] = useState(5);
  const [selectedModel, setSelectedModel] = useState("gemma-2-9b-it");

  const { isEnabled } = useFeatureFlags();
  const showObservability = isEnabled("ENABLE_OBSERVABILITY" as FeatureFlagValue);

  const presets = [
    "Impact of quantum computing on modern RSA cryptography",
    "Latest advancements in fusion energy reactor confinement systems",
    "Telecommunications mesh routing protocols in disaster recovery",
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) return;

    try {
      setLoading(true);
      const res = await fetch(`${appConfig.apiV1Url}/research/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: topic.trim(),
          session_metadata: {
            concurrency_limit: concurrency,
            max_sources_target: maxSources,
            model_target: selectedModel,
          },
        }),
      });

      if (res.ok) {
        const session: ResearchSession = await res.json();
        // Add to history and open it!
        addSession(session);
        setActiveSessionId(session.id);
        setTopic("");
      } else {
        console.error("Failed to create session:", await res.text());
      }
    } catch (err) {
      console.error("Error creating session:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-panel glowing-active rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="font-outfit text-xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </span>
          Launch Research Engine
        </h2>
        <p className="text-xs text-[var(--color-text-secondary)]">
          Deploy deep-learning agents to scrape, summarize, and synthesize a comprehensive intelligence report.
        </p>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
            Research Query
          </label>
          <textarea
            rows={3}
            required
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="E.g., Quantum safe network topologies and post-quantum encryption standards..."
            className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-50)] p-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] transition-colors focus:border-violet-500 focus:outline-none resize-none"
          />
        </div>

        {/* Advanced trigger panel */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 text-xs font-bold text-violet-400 hover:text-violet-300 transition-colors focus:outline-none"
          >
            <svg
              className={["h-3.5 w-3.5 transition-transform duration-200", showAdvanced ? "rotate-90" : ""].join(" ")}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            </svg>
            Advanced Execution Variables
          </button>

          {showAdvanced && (
            <div className="mt-3 rounded-xl bg-[var(--color-surface-50)] p-4 border border-[var(--color-border)] grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[var(--color-text-secondary)]">Concurrency Limit</span>
                  <span className="text-violet-400 font-bold">{concurrency} tasks</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={8}
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value))}
                  className="w-full accent-violet-500 bg-[var(--color-surface-200)]"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[var(--color-text-secondary)]">Max Sources Scraped</span>
                  <span className="text-violet-400 font-bold">{maxSources} sites</span>
                </div>
                <input
                  type="range"
                  min={2}
                  max={15}
                  value={maxSources}
                  onChange={(e) => setMaxSources(parseInt(e.target.value))}
                  className="w-full accent-violet-500 bg-[var(--color-surface-200)]"
                />
              </div>

              <div className="space-y-2 col-span-1 sm:col-span-2 border-t border-[var(--color-border)] pt-3 mt-1">
                <label className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] block mb-1">
                  Target LLM Model Engine
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-200)] p-2.5 text-xs text-white focus:border-violet-500 focus:outline-none"
                >
                  <option value="gemma-2-9b-it">Gemma 2 9B IT (Standard Production)</option>
                  {showObservability && (
                    <option value="gemma-2-27b-it">Gemma 2 27B IT (Experimental High-Fidelity)</option>
                  )}
                </select>
                <p className="text-[9px] text-[var(--color-text-muted)] mt-1">
                  {showObservability 
                    ? "✨ Advanced developer flags active: Gemma 2 27B unlocked for high-fidelity extraction."
                    : "🔒 Gemma 2 27B locked. Enable ENABLE_OBSERVABILITY feature flag to unlock experimental engines."}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Glowing action button */}
        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 py-3 text-sm font-bold text-white shadow-lg shadow-violet-950/30 transition-all hover:scale-[1.01] hover:from-violet-500 hover:to-indigo-500 focus:outline-none disabled:opacity-50 disabled:scale-100 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              <span>Instantiating Agents...</span>
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Deploy Research Workflow</span>
            </>
          )}
        </button>
      </form>

      {/* Preset Suggestions */}
      <div className="space-y-2 border-t border-[var(--color-border)] pt-4">
        <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] block">
          Suggested Investigations
        </span>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setTopic(preset)}
              className="rounded-lg bg-[var(--color-surface-50)] border border-[var(--color-border)] hover:border-violet-500/30 px-3 py-1.5 text-left text-xs text-[var(--color-text-secondary)] hover:text-white transition-all focus:outline-none"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
