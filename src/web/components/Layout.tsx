import { useLocation, Link } from "wouter";
import { ReactNode } from "react";

const NAV = [
  { path: "/", label: "Dashboard", icon: "⬛" },
  { path: "/jobs", label: "All Jobs", icon: "💼" },
  { path: "/runs", label: "Pipeline Runs", icon: "⚡" },
  { path: "/setup", label: "Setup Guide", icon: "📖" },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#0a0f0a" }}>
      {/* Sidebar */}
      <aside
        className="w-[240px] flex-shrink-0 flex flex-col border-r"
        style={{
          background: "#0d150d",
          borderColor: "#1e2e1e",
        }}
      >
        {/* Logo */}
        <div className="px-6 py-6 border-b" style={{ borderColor: "#1e2e1e" }}>
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded flex items-center justify-center text-sm font-bold"
              style={{ background: "#22c55e", color: "#0a0f0a" }}
            >
              J
            </div>
            <div>
              <div
                className="text-sm font-bold leading-none"
                style={{ fontFamily: "Syne, sans-serif", color: "#f0faf0" }}
              >
                JobReach
              </div>
              <div className="text-xs mt-0.5" style={{ color: "#6b9b6b" }}>
                AI Outreach Pipeline
              </div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((item) => {
            const active = location === item.path;
            return (
              <Link key={item.path} href={item.path}>
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all text-sm"
                  style={{
                    background: active ? "#1e2e1e" : "transparent",
                    color: active ? "#22c55e" : "#6b9b6b",
                    fontWeight: active ? 600 : 400,
                    borderLeft: active ? "2px solid #22c55e" : "2px solid transparent",
                  }}
                >
                  <span className="text-base">{item.icon}</span>
                  {item.label}
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t" style={{ borderColor: "#1e2e1e" }}>
          <div className="text-xs" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
            Sukaran Gulati
          </div>
          <div className="text-xs mt-0.5" style={{ color: "#3d6b3d" }}>
            Intern Outreach · 2025
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
