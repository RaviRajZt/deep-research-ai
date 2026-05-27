import { useEffect, useRef } from "react";
import { useResearchStore } from "@/store/research.store";
import { appConfig } from "@/config/app.config";
import { ResearchSession, ExecutionLog } from "@/types/research";

export function useResearchStream(sessionId: string | null) {
  const {
    activeSession,
    logs,
    connectionStatus,
    reconnectAttempt,
    setActiveSession,
    setLogs,
    appendOrUpdateLog,
    setConnectionStatus,
    setReconnectAttempt,
  } = useResearchStore();

  const eventSourceRef = useRef<EventSource | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const backoffDelayRef = useRef<number>(1000); // Start with 1s delay

  // 1. Initial State Fetching (Re-hydration / Resume State)
  useEffect(() => {
    if (!sessionId) return;

    let active = true;

    async function fetchInitialData() {
      try {
        setConnectionStatus("connecting");
        
        // Fetch session status and telemetry
        const sessionRes = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}`);
        if (!sessionRes.ok) throw new Error("Failed to fetch session details");
        const sessionData: ResearchSession = await sessionRes.json();
        
        // Fetch existing execution log timeline
        const logsRes = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}/logs`);
        if (!logsRes.ok) throw new Error("Failed to fetch session timeline");
        const logsData: ExecutionLog[] = await logsRes.json();

        if (active) {
          setActiveSession(sessionData);
          setLogs(logsData);
          
          // Only start SSE stream if session is non-terminal
          const terminalStates = ["completed", "failed", "cancelled"];
          if (!terminalStates.includes(sessionData.status)) {
            connectSSE();
          } else {
            setConnectionStatus("disconnected");
          }
        }
      } catch (err) {
        console.error("Error hydration session state:", err);
        if (active) {
          setConnectionStatus("disconnected");
        }
      }
    }

    fetchInitialData();

    return () => {
      active = false;
      cleanup();
    };
  }, [sessionId]);

  // 2. SSE Stream Lifecycle Management
  function connectSSE() {
    if (!sessionId) return;

    // Clear any active instances
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const streamUrl = `${appConfig.apiV1Url}/research/stream/${sessionId}`;
    console.log(`Connecting to SSE research stream: ${streamUrl}`);
    
    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    // Reset heartbeat timer on connection attempt
    resetHeartbeatTimer();

    es.onopen = () => {
      console.log("SSE Stream connection established.");
      setConnectionStatus("connected");
      setReconnectAttempt(0);
      backoffDelayRef.current = 1000; // Reset backoff
      resetHeartbeatTimer();
    };

    // Generic Message Event (confirmation event)
    es.addEventListener("connected", (event) => {
      console.log("SSE Connected Event:", event.data);
      resetHeartbeatTimer();
    });

    // Session Status Updates
    es.addEventListener("status", async (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("SSE Status Event:", data);
        
        // Fetch the fresh full session data to capture all DB computed states
        const sessionRes = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}`);
        if (sessionRes.ok) {
          const sessionData: ResearchSession = await sessionRes.json();
          setActiveSession(sessionData);
        }
        resetHeartbeatTimer();
      } catch (err) {
        console.error("Error parsing SSE status event:", err);
      }
    });

    // Agent Step Execution Logs
    es.addEventListener("step", (event) => {
      try {
        const data: ExecutionLog = JSON.parse(event.data);
        console.log("SSE Step Log Event:", data);
        appendOrUpdateLog(data);
        resetHeartbeatTimer();
      } catch (err) {
        console.error("Error parsing SSE step event:", err);
      }
    });

    // Terminal Events (Completed / Failed / Cancelled)
    const handleTerminalEvent = async (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`SSE Terminal Event received [${event.type}]:`, data);
        
        // Fetch final session payload
        const sessionRes = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}`);
        if (sessionRes.ok) {
          const sessionData: ResearchSession = await sessionRes.json();
          setActiveSession(sessionData);
        }
        
        // Also fetch the final logs list to capture precise duration_ms and tokens
        const logsRes = await fetch(`${appConfig.apiV1Url}/research/session/${sessionId}/logs`);
        if (logsRes.ok) {
          const logsData: ExecutionLog[] = await logsRes.json();
          setLogs(logsData);
        }

        cleanup();
        setConnectionStatus("disconnected");
      } catch (err) {
        console.error("Error handling SSE terminal event:", err);
      }
    };

    es.addEventListener("completed", handleTerminalEvent);
    es.addEventListener("failed", handleTerminalEvent);
    es.addEventListener("cancelled", handleTerminalEvent);

    // Heartbeat Pings
    es.addEventListener("ping", () => {
      console.log("SSE Heartbeat ping received.");
      resetHeartbeatTimer();
    });

    es.onerror = (err) => {
      console.warn("SSE stream error occurred:", err);
      es.close();
      
      // Auto-Reconnect Logic with Exponential Backoff
      setConnectionStatus("reconnecting");
      const nextAttempt = reconnectAttempt + 1;
      setReconnectAttempt(nextAttempt);
      
      const delay = backoffDelayRef.current;
      console.log(`Scheduling stream reconnect attempt ${nextAttempt} in ${delay}ms...`);
      
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      
      reconnectTimerRef.current = setTimeout(() => {
        // Increase delay exponentially up to 16 seconds max
        backoffDelayRef.current = Math.min(delay * 2, 16000);
        connectSSE();
      }, delay);
    };
  }

  // 3. Heartbeat Timeout / Watchdog Timer
  // If the server doesn't send *any* message or ping for 15 seconds (heartbeat is 5s),
  // we assume the connection is dead/zombie and trigger a reconnect.
  function resetHeartbeatTimer() {
    if (heartbeatTimerRef.current) clearTimeout(heartbeatTimerRef.current);
    
    heartbeatTimerRef.current = setTimeout(() => {
      console.warn("Heartbeat timeout expired. Stream connection is stale. Reconnecting...");
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      setConnectionStatus("reconnecting");
      setReconnectAttempt(reconnectAttempt + 1);
      connectSSE();
    }, 15000);
  }

  // 4. Cleanup & Tear Down
  function cleanup() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearTimeout(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }

  return {
    activeSession,
    logs,
    connectionStatus,
    reconnectAttempt,
  };
}
