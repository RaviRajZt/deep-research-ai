import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { ResearchSession, ExecutionLog } from "@/types/research";

interface ResearchState {
  // ---------- State ----------
  sessions: ResearchSession[];
  activeSessionId: string | null;
  activeSession: ResearchSession | null;
  logs: ExecutionLog[];
  connectionStatus: "disconnected" | "connecting" | "connected" | "reconnecting";
  reconnectAttempt: number;

  // ---------- Actions ----------
  setSessions: (sessions: ResearchSession[]) => void;
  addSession: (session: ResearchSession) => void;
  setActiveSessionId: (id: string | null) => void;
  setActiveSession: (session: ResearchSession | null) => void;
  setLogs: (logs: ExecutionLog[]) => void;
  appendOrUpdateLog: (log: ExecutionLog) => void;
  setConnectionStatus: (status: "disconnected" | "connecting" | "connected" | "reconnecting") => void;
  setReconnectAttempt: (attempt: number) => void;
  resetActiveSession: () => void;
}

export const useResearchStore = create<ResearchState>()(
  devtools(
    (set) => ({
      // Defaults
      sessions: [],
      activeSessionId: null,
      activeSession: null,
      logs: [],
      connectionStatus: "disconnected",
      reconnectAttempt: 0,

      // Actions
      setSessions: (sessions) => set({ sessions }, false, "setSessions"),
      
      addSession: (session) =>
        set(
          (state) => ({ sessions: [session, ...state.sessions] }),
          false,
          "addSession"
        ),

      setActiveSessionId: (activeSessionId) =>
        set(
          (state) => {
            // Reset active states if ID is changing
            if (state.activeSessionId !== activeSessionId) {
              return {
                activeSessionId,
                activeSession: null,
                logs: [],
                connectionStatus: "disconnected",
                reconnectAttempt: 0,
              };
            }
            return { activeSessionId };
          },
          false,
          "setActiveSessionId"
        ),

      setActiveSession: (activeSession) =>
        set(
          (state) => {
            // If the active session is updated, we also update its copy inside the main history list
            const updatedSessions = state.sessions.map((s) =>
              s.id === activeSession?.id ? { ...s, ...activeSession } : s
            );
            return {
              activeSession,
              sessions: updatedSessions,
            };
          },
          false,
          "setActiveSession"
        ),

      setLogs: (logs) =>
        set(
          () => {
            // Sort logs by step_order first, then created_at
            const sorted = [...logs].sort((a, b) => {
              if (a.step_order !== null && b.step_order !== null) {
                return a.step_order - b.step_order;
              }
              return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
            });
            return { logs: sorted };
          },
          false,
          "setLogs"
        ),

      appendOrUpdateLog: (log) =>
        set(
          (state) => {
            const exists = state.logs.some((l) => l.id === log.id);
            let newLogs;
            if (exists) {
              newLogs = state.logs.map((l) => (l.id === log.id ? { ...l, ...log } : l));
            } else {
              newLogs = [...state.logs, log];
            }
            
            // Re-sort
            newLogs.sort((a, b) => {
              if (a.step_order !== null && b.step_order !== null) {
                return a.step_order - b.step_order;
              }
              return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
            });

            // Also check if this step update represents a change in the active session's overall status
            const updatedSession = state.activeSession;
            if (updatedSession && log.status === "failed") {
              // If a core step failed, the session status might need updating (though backend handles it)
            }

            return { logs: newLogs, activeSession: updatedSession };
          },
          false,
          "appendOrUpdateLog"
        ),

      setConnectionStatus: (connectionStatus) =>
        set({ connectionStatus }, false, "setConnectionStatus"),

      setReconnectAttempt: (reconnectAttempt) =>
        set({ reconnectAttempt }, false, "setReconnectAttempt"),

      resetActiveSession: () =>
        set(
          {
            activeSessionId: null,
            activeSession: null,
            logs: [],
            connectionStatus: "disconnected",
            reconnectAttempt: 0,
          },
          false,
          "resetActiveSession"
        ),
    }),
    { name: "ResearchStore" }
  )
);
