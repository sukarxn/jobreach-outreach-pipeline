const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  pending:           { label: "Pending",    color: "#9ca3af", bg: "#1f2937" },
  scraped:           { label: "Scraped",    color: "#9ca3af", bg: "#1f2937" },
  message_generated: { label: "Ready",      color: "#60a5fa", bg: "#1e3a5f" },
  sent_manually:     { label: "Sent",       color: "#fbbf24", bg: "#3d2c00" },
  replied:           { label: "Replied",    color: "#22c55e", bg: "#0d2e1a" },
  no_reply:          { label: "No Reply",   color: "#f87171", bg: "#2e1515" },
  interview:         { label: "Interview",  color: "#c084fc", bg: "#2d1b4e" },
  filtered_out:      { label: "Filtered",   color: "#6b7280", bg: "#161616" },
  scrape_only:       { label: "Scrape Only",color: "#6b7280", bg: "#161616" },
};

export default function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG["pending"];
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
      style={{
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}33`,
        fontFamily: "DM Sans, sans-serif",
      }}
    >
      {cfg.label}
    </span>
  );
}
