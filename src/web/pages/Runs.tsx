import { useQuery } from "@tanstack/react-query";

interface Run {
  id: number;
  runAt: string;
  status: string;
  jobsScraped: number;
  jobsAccepted: number;
  messagesGenerated: number;
  durationSeconds: number;
  errorMessage: string;
}

function RunRow({ run }: { run: Run }) {
  const statusColor = run.status === "completed" ? "#22c55e" : run.status === "failed" ? "#ef4444" : "#fbbf24";

  return (
    <div
      className="rounded-xl border px-5 py-4 transition-all"
      style={{ background: "#111a11", borderColor: "#1e2e1e" }}
    >
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}66` }}
          />
          <div>
            <div className="text-sm font-medium" style={{ color: "#f0faf0" }}>
              Run #{run.id}
              <span
                className="ml-2 text-xs px-2 py-0.5 rounded"
                style={{ background: `${statusColor}22`, color: statusColor, border: `1px solid ${statusColor}44` }}
              >
                {run.status}
              </span>
            </div>
            <div className="text-xs mt-0.5" style={{ color: "#6b9b6b", fontFamily: "JetBrains Mono, monospace" }}>
              {run.runAt ? new Date(run.runAt).toLocaleString() : "—"}
              {run.durationSeconds && <span className="ml-2">{run.durationSeconds}s</span>}
            </div>
          </div>
        </div>

        <div className="flex gap-6 text-sm">
          <div className="text-center">
            <div className="font-bold" style={{ color: "#f0faf0" }}>{run.jobsScraped ?? 0}</div>
            <div className="text-xs" style={{ color: "#6b9b6b" }}>Scraped</div>
          </div>
          <div className="text-center">
            <div className="font-bold" style={{ color: "#60a5fa" }}>{run.jobsAccepted ?? 0}</div>
            <div className="text-xs" style={{ color: "#6b9b6b" }}>Accepted</div>
          </div>
          <div className="text-center">
            <div className="font-bold" style={{ color: "#22c55e" }}>{run.messagesGenerated ?? 0}</div>
            <div className="text-xs" style={{ color: "#6b9b6b" }}>Messages</div>
          </div>
        </div>
      </div>

      {run.errorMessage && (
        <div
          className="mt-3 text-xs px-3 py-2 rounded"
          style={{ background: "#2e1515", color: "#f87171", border: "1px solid #ef444433" }}
        >
          {run.errorMessage}
        </div>
      )}
    </div>
  );
}

export default function Runs() {
  const { data, isLoading } = useQuery<{ runs: Run[] }>({
    queryKey: ["runs"],
    queryFn: async () => {
      const r = await fetch("/api/runs");
      return r.json();
    },
    refetchInterval: 15_000,
  });

  const runs = data?.runs || [];

  return (
    <div className="p-8">
      <div className="mb-6 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: "Syne, sans-serif" }}>
          Pipeline Runs
        </h1>
        <p className="text-sm" style={{ color: "#6b9b6b" }}>
          History of all scraper + message generation runs
        </p>
      </div>

      {/* Cron schedule reminder */}
      <div
        className="rounded-xl border p-5 mb-6 animate-fade-in-up animate-delay-100"
        style={{ background: "#111a11", borderColor: "#1e2e1e" }}
      >
        <div className="text-xs uppercase tracking-widest mb-3" style={{ color: "#6b9b6b", fontFamily: "JetBrains Mono, monospace" }}>
          Cron Schedule
        </div>
        <div className="flex gap-3 flex-wrap">
          {["9:00 AM", "2:00 PM", "7:00 PM"].map((time) => (
            <div
              key={time}
              className="flex items-center gap-2 px-3 py-2 rounded-lg"
              style={{ background: "#162016", border: "1px solid #1e2e1e" }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#22c55e" }} />
              <span className="text-sm font-medium" style={{ color: "#f0faf0", fontFamily: "JetBrains Mono, monospace" }}>
                {time}
              </span>
            </div>
          ))}
          <div className="flex items-center text-xs" style={{ color: "#6b9b6b" }}>
            · Every 5 hours · Last 5 hours of postings
          </div>
        </div>
      </div>

      {/* Runs list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-xl h-20 animate-pulse" style={{ background: "#111a11" }} />
          ))}
        </div>
      ) : runs.length === 0 ? (
        <div className="rounded-xl p-12 border text-center" style={{ background: "#111a11", borderColor: "#1e2e1e" }}>
          <div className="text-4xl mb-3">⚡</div>
          <div className="font-medium mb-1" style={{ color: "#f0faf0" }}>No runs yet</div>
          <div className="text-sm" style={{ color: "#6b9b6b" }}>
            Run <code className="px-1 py-0.5 rounded text-xs" style={{ background: "#162016", color: "#22c55e" }}>python main.py</code> to start
          </div>
        </div>
      ) : (
        <div className="space-y-2 animate-fade-in-up animate-delay-200">
          {runs.map((run) => (
            <RunRow key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
