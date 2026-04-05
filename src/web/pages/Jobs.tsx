import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import StatusBadge from "../components/StatusBadge";

interface Job {
  id: string;
  jobTitle: string;
  companyName: string;
  location: string;
  postedAt: string;
  jobUrl: string;
  applyUrl: string;
  recruiterName: string;
  recruiterTitle: string;
  recruiterPhoto: string;
  recruiterLinkedin: string;
  outreachMessage: string;
  messageStatus: string;
  scrapedAt: string;
  notes: string;
  descriptionText: string;
  applicantsCount: string;
}

const STATUS_OPTIONS = [
  { value: "pending", label: "Pending" },
  { value: "message_generated", label: "Message Ready" },
  { value: "sent_manually", label: "Sent Manually" },
  { value: "replied", label: "Replied" },
  { value: "no_reply", label: "No Reply" },
  { value: "interview", label: "Got Interview" },
  { value: "filtered_out", label: "Filtered Out" },
];

function JobCard({ job, onStatusChange }: { job: Job; onStatusChange: (id: string, status: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyMessage = () => {
    if (job.outreachMessage) {
      navigator.clipboard.writeText(job.outreachMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className="rounded-xl border transition-all"
      style={{ background: "#111a11", borderColor: expanded ? "#22c55e44" : "#1e2e1e" }}
    >
      {/* Header row */}
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5 flex-wrap">
            <span className="font-semibold text-sm" style={{ color: "#f0faf0" }}>
              {job.jobTitle || "Untitled Role"}
            </span>
            <StatusBadge status={job.messageStatus || "pending"} />
          </div>
          <div className="text-sm" style={{ color: "#6b9b6b" }}>
            {job.companyName}
            {job.location && <span className="mx-1">·</span>}
            {job.location}
            {job.applicantsCount && (
              <span className="ml-2 text-xs" style={{ color: "#3d6b3d" }}>
                {job.applicantsCount} applicants
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {job.recruiterName && (
            <span className="text-xs hidden sm:block" style={{ color: "#6b9b6b" }}>
              👤 {job.recruiterName}
            </span>
          )}
          <span className="text-xs" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
            {job.scrapedAt ? new Date(job.scrapedAt).toLocaleDateString() : ""}
          </span>
          <span style={{ color: "#3d6b3d" }}>{expanded ? "▲" : "▼"}</span>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t px-5 py-4 space-y-4" style={{ borderColor: "#1e2e1e" }}>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Left: Job info */}
            <div className="space-y-3">
              <div>
                <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
                  Job
                </div>
                <div className="flex gap-2 flex-wrap">
                  {job.jobUrl && (
                    <a
                      href={job.jobUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-3 py-1.5 rounded-lg"
                      style={{ background: "#162016", color: "#22c55e", border: "1px solid #1e2e1e" }}
                    >
                      View Posting ↗
                    </a>
                  )}
                  {job.applyUrl && job.applyUrl !== job.jobUrl && (
                    <a
                      href={job.applyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-3 py-1.5 rounded-lg"
                      style={{ background: "#162016", color: "#fbbf24", border: "1px solid #1e2e1e" }}
                    >
                      Apply Here ↗
                    </a>
                  )}
                </div>
                {job.postedAt && (
                  <div className="text-xs mt-2" style={{ color: "#6b9b6b" }}>
                    Posted: {job.postedAt}
                  </div>
                )}
              </div>

              {/* Recruiter */}
              <div>
                <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
                  Recruiter
                </div>
                <div className="flex items-center gap-2">
                  {job.recruiterPhoto && (
                    <img
                      src={job.recruiterPhoto}
                      alt={job.recruiterName}
                      className="w-8 h-8 rounded-full object-cover"
                      style={{ border: "1px solid #1e2e1e" }}
                    />
                  )}
                  <div>
                    <div className="text-sm font-medium" style={{ color: "#f0faf0" }}>
                      {job.recruiterName || "—"}
                    </div>
                    {job.recruiterTitle && (
                      <div className="text-xs" style={{ color: "#6b9b6b" }}>{job.recruiterTitle}</div>
                    )}
                  </div>
                </div>
                {job.recruiterLinkedin && (
                  <a
                    href={job.recruiterLinkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 text-xs px-3 py-1.5 rounded-lg"
                    style={{ background: "#0d2040", color: "#60a5fa", border: "1px solid #1e3a5f" }}
                  >
                    LinkedIn Profile ↗
                  </a>
                )}
              </div>

              {/* Status update */}
              <div>
                <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
                  Update Status
                </div>
                <select
                  className="text-sm rounded-lg px-3 py-1.5 w-full"
                  style={{
                    background: "#162016",
                    color: "#f0faf0",
                    border: "1px solid #1e2e1e",
                    fontFamily: "DM Sans, sans-serif",
                  }}
                  value={job.messageStatus || "pending"}
                  onChange={(e) => onStatusChange(job.id, e.target.value)}
                >
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Right: Message */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs uppercase tracking-widest" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
                  Outreach Message
                </div>
                {job.outreachMessage && (
                  <button
                    onClick={copyMessage}
                    className="text-xs px-2 py-1 rounded"
                    style={{ background: copied ? "#0d2e1a" : "#162016", color: copied ? "#22c55e" : "#6b9b6b" }}
                  >
                    {copied ? "✓ Copied" : "Copy"}
                  </button>
                )}
              </div>
              {job.outreachMessage ? (
                <textarea
                  readOnly
                  value={job.outreachMessage}
                  rows={6}
                  className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                  style={{
                    background: "#0d150d",
                    color: "#d1fae5",
                    border: "1px solid #1e2e1e",
                    fontFamily: "DM Sans, sans-serif",
                    lineHeight: "1.6",
                  }}
                />
              ) : (
                <div
                  className="rounded-lg px-3 py-4 text-sm text-center"
                  style={{ background: "#0d150d", color: "#3d6b3d", border: "1px solid #1e2e1e" }}
                >
                  No message generated yet
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Jobs() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery<{ jobs: Job[] }>({
    queryKey: ["jobs", statusFilter, search],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (search) params.set("search", search);
      params.set("limit", "200");
      const r = await fetch(`/api/jobs?${params}`);
      return r.json();
    },
  });

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const r = await fetch(`/api/jobs/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      return r.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  const jobs = data?.jobs || [];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 animate-fade-in-up">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: "Syne, sans-serif" }}>
            All Jobs
          </h1>
          <p className="text-sm" style={{ color: "#6b9b6b" }}>
            {jobs.length} jobs · click any row to expand
          </p>
        </div>
        <a
          href="/api/export/csv"
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
          style={{ background: "#22c55e", color: "#0a0f0a" }}
        >
          ⬇ Export CSV
        </a>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap animate-fade-in-up animate-delay-100">
        <input
          type="text"
          placeholder="Search title, company, recruiter..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-48 text-sm px-4 py-2 rounded-lg"
          style={{
            background: "#111a11",
            color: "#f0faf0",
            border: "1px solid #1e2e1e",
            fontFamily: "DM Sans, sans-serif",
          }}
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-sm px-4 py-2 rounded-lg"
          style={{
            background: "#111a11",
            color: "#f0faf0",
            border: "1px solid #1e2e1e",
            fontFamily: "DM Sans, sans-serif",
          }}
        >
          <option value="all">All Statuses</option>
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Jobs list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="rounded-xl h-20 animate-pulse" style={{ background: "#111a11" }} />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-xl p-12 border text-center" style={{ background: "#111a11", borderColor: "#1e2e1e" }}>
          <div className="text-4xl mb-3">📭</div>
          <div className="font-medium mb-1" style={{ color: "#f0faf0" }}>No jobs found</div>
          <div className="text-sm" style={{ color: "#6b9b6b" }}>
            {search || statusFilter !== "all" ? "Try clearing filters" : "Run the pipeline to scrape jobs"}
          </div>
        </div>
      ) : (
        <div className="space-y-2 animate-fade-in-up animate-delay-200">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onStatusChange={(id, status) => statusMutation.mutate({ id, status })}
            />
          ))}
        </div>
      )}
    </div>
  );
}
