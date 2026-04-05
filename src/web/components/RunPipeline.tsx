import { useState, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

type AgentStatus = "unknown" | "online" | "offline" | "running";

const STORAGE_KEY = "agent_url";
const DEFAULT_URL = "http://localhost:5050";

export default function RunPipeline() {
  const qc = useQueryClient();
  const [agentUrl, setAgentUrl] = useState(() => localStorage.getItem(STORAGE_KEY) || DEFAULT_URL);
  const [editingUrl, setEditingUrl] = useState(false);
  const [draftUrl, setDraftUrl] = useState(agentUrl);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>("unknown");
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  // Poll agent health every 5s
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${agentUrl}/health`, { signal: AbortSignal.timeout(3000) });
        if (r.ok) {
          const data = await r.json();
          setAgentStatus(data.is_running ? "running" : "online");
          setIsRunning(data.is_running);
        } else {
          setAgentStatus("offline");
        }
      } catch {
        setAgentStatus("offline");
      }
    };
    check();
    const t = setInterval(check, 5000);
    return () => clearInterval(t);
  }, [agentUrl]);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const saveUrl = () => {
    const url = draftUrl.replace(/\/$/, "");
    setAgentUrl(url);
    localStorage.setItem(STORAGE_KEY, url);
    setEditingUrl(false);
  };

  const startRun = async () => {
    if (isRunning) return;
    setLogs([]);
    setShowLogs(true);
    setIsRunning(true);
    setAgentStatus("running");

    // Trigger the run
    try {
      const r = await fetch(`${agentUrl}/run`, {
        method: "POST",
        signal: AbortSignal.timeout(5000),
      });
      if (!r.ok) {
        const err = await r.json();
        if (err.error === "already_running") {
          setLogs(["[agent] Pipeline is already running — connecting to log stream..."]);
        } else {
          setLogs([`[agent] Error: ${err.error}`]);
          setIsRunning(false);
          setAgentStatus("online");
          return;
        }
      }
    } catch (e) {
      setLogs(["[agent] Could not reach local agent. Is it running? See Setup Guide."]);
      setIsRunning(false);
      setAgentStatus("offline");
      return;
    }

    // Connect SSE log stream
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${agentUrl}/logs`);
    esRef.current = es;

    es.onmessage = (e) => {
      const line = e.data;
      setLogs((prev) => [...prev, line]);
      if (line.includes("[agent] DONE")) {
        es.close();
        setIsRunning(false);
        setAgentStatus("online");
        // Refresh dashboard data
        setTimeout(() => {
          qc.invalidateQueries({ queryKey: ["stats"] });
          qc.invalidateQueries({ queryKey: ["jobs"] });
          qc.invalidateQueries({ queryKey: ["jobs-recent"] });
          qc.invalidateQueries({ queryKey: ["runs"] });
        }, 1500);
      }
    };

    es.onerror = () => {
      es.close();
      setIsRunning(false);
      setAgentStatus("offline");
      setLogs((prev) => [...prev, "[agent] Log stream disconnected."]);
    };
  };

  const stopStream = () => {
    esRef.current?.close();
    setIsRunning(false);
  };

  const statusDot: Record<AgentStatus, { color: string; label: string; glow: string }> = {
    unknown: { color: "#6b7280", label: "Checking...", glow: "none" },
    online:  { color: "#22c55e", label: "Agent online", glow: "0 0 8px #22c55e66" },
    offline: { color: "#ef4444", label: "Agent offline", glow: "0 0 8px #ef444466" },
    running: { color: "#fbbf24", label: "Running...", glow: "0 0 8px #fbbf2466" },
  };

  const dot = statusDot[agentStatus];

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ background: "#111a11", borderColor: agentStatus === "online" || agentStatus === "running" ? "#22c55e33" : "#1e2e1e" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
            style={{ background: "#0d150d", border: "1px solid #1e2e1e" }}
          >
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{
                background: dot.color,
                boxShadow: dot.glow,
                animation: agentStatus === "running" ? "pulse 1.5s infinite" : "none",
              }}
            />
            <span className="text-xs" style={{ color: dot.color, fontFamily: "JetBrains Mono, monospace" }}>
              {dot.label}
            </span>
          </div>

          {/* Agent URL — inline edit */}
          {editingUrl ? (
            <div className="flex items-center gap-2">
              <input
                autoFocus
                value={draftUrl}
                onChange={(e) => setDraftUrl(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") saveUrl(); if (e.key === "Escape") setEditingUrl(false); }}
                className="text-xs px-2 py-1 rounded"
                style={{
                  background: "#162016",
                  color: "#f0faf0",
                  border: "1px solid #22c55e55",
                  fontFamily: "JetBrains Mono, monospace",
                  width: 220,
                }}
              />
              <button onClick={saveUrl} className="text-xs px-2 py-1 rounded" style={{ background: "#22c55e", color: "#0a0f0a" }}>
                Save
              </button>
              <button onClick={() => setEditingUrl(false)} className="text-xs px-2 py-1 rounded" style={{ background: "#162016", color: "#6b9b6b" }}>
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setDraftUrl(agentUrl); setEditingUrl(true); }}
              className="text-xs"
              style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}
              title="Click to edit agent URL"
            >
              {agentUrl} ✎
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {showLogs && logs.length > 0 && (
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="text-xs px-3 py-1.5 rounded-lg"
              style={{ background: "#162016", color: "#6b9b6b", border: "1px solid #1e2e1e" }}
            >
              {showLogs ? "Hide logs" : "Show logs"}
            </button>
          )}

          <button
            onClick={isRunning ? stopStream : startRun}
            disabled={agentStatus === "offline" || agentStatus === "unknown"}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
            style={{
              background: isRunning
                ? "#2e1515"
                : agentStatus === "offline" || agentStatus === "unknown"
                ? "#162016"
                : "#22c55e",
              color: isRunning
                ? "#ef4444"
                : agentStatus === "offline" || agentStatus === "unknown"
                ? "#3d6b3d"
                : "#0a0f0a",
              border: isRunning ? "1px solid #ef444444" : "none",
              cursor: agentStatus === "offline" || agentStatus === "unknown" ? "not-allowed" : "pointer",
              fontFamily: "Syne, sans-serif",
            }}
          >
            {isRunning ? (
              <>
                <span
                  className="w-3 h-3 rounded-full border-2 border-t-transparent animate-spin"
                  style={{ borderColor: "#ef444466", borderTopColor: "transparent" }}
                />
                Running...
              </>
            ) : (
              <>
                <span>⚡</span>
                Run Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Log terminal */}
      {showLogs && (
        <div
          className="border-t"
          style={{ borderColor: "#1e2e1e" }}
        >
          <div
            className="flex items-center justify-between px-5 py-2"
            style={{ background: "#0d150d" }}
          >
            <span className="text-xs" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
              pipeline output
            </span>
            <button
              onClick={() => setLogs([])}
              className="text-xs"
              style={{ color: "#3d6b3d" }}
            >
              clear
            </button>
          </div>
          <div
            className="px-5 py-3 overflow-y-auto"
            style={{
              background: "#070c07",
              maxHeight: 280,
              fontFamily: "JetBrains Mono, monospace",
              fontSize: 12,
              lineHeight: "1.7",
            }}
          >
            {logs.length === 0 ? (
              <span style={{ color: "#3d6b3d" }}>Waiting for output...</span>
            ) : (
              logs.map((line, i) => {
                const color = line.includes("ERROR") || line.includes("✗")
                  ? "#f87171"
                  : line.includes("✓") || line.includes("COMPLETE") || line.includes("DONE")
                  ? "#22c55e"
                  : line.includes("WARN") || line.includes("⚠")
                  ? "#fbbf24"
                  : line.includes("[agent]")
                  ? "#6b9b6b"
                  : "#d1fae5";
                return (
                  <div key={i} style={{ color }}>
                    {line}
                  </div>
                );
              })
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      )}

      {/* Offline help */}
      {agentStatus === "offline" && (
        <div
          className="mx-5 mb-4 rounded-lg px-4 py-3 text-xs"
          style={{ background: "#2e1515", color: "#f87171", border: "1px solid #ef444433" }}
        >
          Agent offline — run <code className="mx-1 px-1 rounded" style={{ background: "#1a0a0a" }}>python agent.py</code>
          in your <code className="mx-1 px-1 rounded" style={{ background: "#1a0a0a" }}>job-outreach</code> folder, then refresh.
        </div>
      )}
    </div>
  );
}
