import { useQuery } from "@tanstack/react-query";
import StatusBadge from "../components/StatusBadge";
import RunPipeline from "../components/RunPipeline";

interface Stats {
  total: number;
  todayScraped: number;
  messagesGenerated: number;
  sentManually: number;
  replied: number;
  noReply: number;
  interview: number;
  filteredOut: number;
}

interface Job {
  id: string;
  jobTitle: string;
  companyName: string;
  location: string;
  recruiterName: string;
  recruiterLinkedin: string;
  outreachMessage: string;
  messageStatus: string;
  scrapedAt: string;
  jobUrl: string;
}

function MetricCard({ label, value, sub, accent }: { label: string; value: number | string; sub?: string; accent?: boolean }) {
  return (
    <div
      className="rounded-xl p-5 border transition-all"
      style={{
        background: "#111a11",
        borderColor: accent ? "#22c55e44" : "#1e2e1e",
        boxShadow: accent ? "0 0 20px #22c55e15" : "none",
      }}
    >
      <div className="text-xs mb-2 uppercase tracking-widest" style={{ color: "#6b9b6b", fontFamily: "JetBrains Mono, monospace" }}>
        {label}
      </div>
      <div
        className="text-3xl font-bold"
        style={{ color: accent ? "#22c55e" : "#f0faf0", fontFamily: "Syne, sans-serif" }}
      >
        {value}
      </div>
      {sub && <div className="text-xs mt-1" style={{ color: "#3d6b3d" }}>{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { data: statsData } = useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: async () => {
      const r = await fetch("/api/stats");
      return r.json();
    },
    refetchInterval: 30_000,
  });

  const { data: jobsData } = useQuery<{ jobs: Job[] }>({
    queryKey: ["jobs-recent"],
    queryFn: async () => {
      const r = await fetch("/api/jobs?limit=8");
      return r.json();
    },
    refetchInterval: 30_000,
  });

  const stats = statsData;
  const recentJobs = jobsData?.jobs || [];

  const replyRate = stats && stats.sentManually > 0
    ? Math.round((stats.replied / stats.sentManually) * 100)
    : 0;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: "Syne, sans-serif", color: "#f0faf0" }}>
          Outreach Dashboard
        </h1>
        <p className="text-sm" style={{ color: "#6b9b6b" }}>
          {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </p>
      </div>

      {/* Run pipeline */}
      <div className="mb-6 animate-fade-in-up animate-delay-100">
        <RunPipeline />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-4 mb-8 lg:grid-cols-4 animate-fade-in-up animate-delay-100">
        <MetricCard label="Scraped Today" value={stats?.todayScraped ?? "—"} sub="new postings" accent />
        <MetricCard label="Messages Ready" value={stats?.messagesGenerated ?? "—"} sub="ready to send" />
        <MetricCard label="Sent Manually" value={stats?.sentManually ?? "—"} sub="outreach done" />
        <MetricCard label="Interviews" value={stats?.interview ?? "—"} sub="booking calls" />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-10 lg:grid-cols-4 animate-fade-in-up animate-delay-200">
        <MetricCard label="Total Jobs" value={stats?.total ?? "—"} />
        <MetricCard label="Replied" value={stats?.replied ?? "—"} />
        <MetricCard label="No Reply" value={stats?.noReply ?? "—"} />
        <MetricCard
          label="Reply Rate"
          value={`${replyRate}%`}
          sub={stats?.sentManually ? `of ${stats.sentManually} sent` : "no sends yet"}
        />
      </div>

      {/* Pipeline status bar */}
      {stats && stats.total > 0 && (
        <div className="mb-10 rounded-xl p-5 border animate-fade-in-up animate-delay-300" style={{ background: "#111a11", borderColor: "#1e2e1e" }}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs uppercase tracking-widest" style={{ color: "#6b9b6b", fontFamily: "JetBrains Mono, monospace" }}>
              Pipeline Funnel
            </span>
            <span className="text-xs" style={{ color: "#3d6b3d" }}>{stats.total} total jobs</span>
          </div>
          <div className="flex gap-1 h-2 rounded overflow-hidden">
            {[
              { val: stats.messagesGenerated, color: "#3b82f6" },
              { val: stats.sentManually,       color: "#f59e0b" },
              { val: stats.replied,             color: "#22c55e" },
              { val: stats.interview,           color: "#a855f7" },
              { val: stats.noReply,             color: "#ef4444" },
              { val: stats.filteredOut,         color: "#1e2e1e" },
            ].map((seg, i) => (
              <div
                key={i}
                style={{
                  flex: seg.val,
                  background: seg.color,
                  minWidth: seg.val > 0 ? 2 : 0,
                }}
              />
            ))}
          </div>
          <div className="flex gap-4 mt-3 flex-wrap">
            {[
              { label: "Ready", color: "#3b82f6", val: stats.messagesGenerated },
              { label: "Sent", color: "#f59e0b", val: stats.sentManually },
              { label: "Replied", color: "#22c55e", val: stats.replied },
              { label: "Interview", color: "#a855f7", val: stats.interview },
              { label: "No Reply", color: "#ef4444", val: stats.noReply },
            ].map((l) => (
              <span key={l.label} className="flex items-center gap-1.5 text-xs" style={{ color: "#6b9b6b" }}>
                <span className="w-2 h-2 rounded-full inline-block" style={{ background: l.color }} />
                {l.label} <span style={{ color: "#f0faf0" }}>{l.val}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent jobs */}
      <div className="animate-fade-in-up animate-delay-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold" style={{ fontFamily: "Syne, sans-serif" }}>Recent Jobs</h2>
          <a href="/jobs" className="text-xs" style={{ color: "#22c55e" }}>View all →</a>
        </div>

        {recentJobs.length === 0 ? (
          <div className="rounded-xl p-12 border text-center" style={{ background: "#111a11", borderColor: "#1e2e1e" }}>
            <div className="text-4xl mb-3">🚀</div>
            <div className="font-medium mb-1" style={{ color: "#f0faf0" }}>No jobs yet</div>
            <div className="text-sm" style={{ color: "#6b9b6b" }}>Run the Python pipeline to start scraping</div>
            <a href="/setup" className="inline-block mt-4 text-xs px-4 py-2 rounded-lg" style={{ background: "#1e2e1e", color: "#22c55e" }}>
              View setup guide →
            </a>
          </div>
        ) : (
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <div
                key={job.id}
                className="rounded-xl border px-5 py-4 transition-all"
                style={{ background: "#111a11", borderColor: "#1e2e1e" }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm truncate" style={{ color: "#f0faf0" }}>
                        {job.jobTitle || "Untitled Role"}
                      </span>
                      <StatusBadge status={job.messageStatus || "pending"} />
                    </div>
                    <div className="text-sm" style={{ color: "#6b9b6b" }}>
                      {job.companyName} · {job.location}
                    </div>
                    {job.recruiterName && (
                      <div className="text-xs mt-1" style={{ color: "#3d6b3d" }}>
                        👤 {job.recruiterName}
                        {job.recruiterLinkedin && (
                          <a
                            href={job.recruiterLinkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-2"
                            style={{ color: "#22c55e" }}
                          >
                            LinkedIn ↗
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-xs flex-shrink-0" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
                    {job.scrapedAt ? new Date(job.scrapedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
