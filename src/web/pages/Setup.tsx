function CodeBlock({ code, lang = "" }: { code: string; lang?: string }) {
  const copy = () => navigator.clipboard.writeText(code);
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #1e2e1e" }}>
      <div className="flex items-center justify-between px-4 py-2" style={{ background: "#0d150d" }}>
        <span className="text-xs" style={{ color: "#3d6b3d", fontFamily: "JetBrains Mono, monospace" }}>
          {lang}
        </span>
        <button
          onClick={copy}
          className="text-xs px-2 py-1 rounded"
          style={{ background: "#162016", color: "#6b9b6b" }}
        >
          Copy
        </button>
      </div>
      <pre
        className="px-4 py-3 text-xs overflow-x-auto"
        style={{
          background: "#0a0f0a",
          color: "#d1fae5",
          fontFamily: "JetBrains Mono, monospace",
          lineHeight: "1.6",
        }}
      >
        {code}
      </pre>
    </div>
  );
}

function Step({ number, title, children }: { number: string; title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-3">
        <span
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
          style={{ background: "#22c55e", color: "#0a0f0a", fontFamily: "Syne, sans-serif" }}
        >
          {number}
        </span>
        <h3 className="text-base font-bold" style={{ fontFamily: "Syne, sans-serif", color: "#f0faf0" }}>
          {title}
        </h3>
      </div>
      <div className="pl-10 space-y-3">{children}</div>
    </div>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-sm" style={{ color: "#6b9b6b", lineHeight: "1.7" }}>{children}</p>;
}

export default function Setup() {
  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ fontFamily: "Syne, sans-serif" }}>
          Setup Guide
        </h1>
        <p className="text-sm" style={{ color: "#6b9b6b" }}>
          Get the Python pipeline running in ~10 minutes
        </p>
      </div>

      <div className="animate-fade-in-up animate-delay-100">

        <Step number="1" title="Start the local agent (enables Run Now button)">
          <P>The agent is a tiny local server that lets the dashboard trigger your pipeline and stream logs live. Run it once — keep it running alongside the pipeline.</P>
          <CodeBlock lang="bash" code={`cd job-outreach\npython agent.py`} />
          <CodeBlock lang="output" code={`  JobReach Local Agent\n  ─────────────────────────────────\n  Listening on  http://localhost:5050\n  Keep this running while using the dashboard.`} />
          <P>The dashboard auto-detects it at <code className="text-green-400">http://localhost:5050</code>. You can change the port via the <code className="text-green-400">AGENT_PORT</code> env var, and update the URL in the Run Now bar on the dashboard.</P>
          <P>Optional: set <code className="text-green-400">AGENT_SECRET=some_token</code> in .env to require auth for run triggers.</P>
        </Step>

        <Step number="2" title="Clone the pipeline project">
          <P>The Python pipeline lives at <code className="text-green-400">/home/user/job-outreach</code> in this sandbox. Download it or copy files to your local machine.</P>
          <CodeBlock lang="bash" code={`# Install dependencies\ncd job-outreach\npip install -r requirements.txt`} />
        </Step>

        <Step number="3" title="Set up API keys in .env">
          <P>Copy the example file and fill in your 4 keys:</P>
          <CodeBlock lang="bash" code={`cp .env.example .env\n# Edit .env with your keys`} />
          <CodeBlock lang=".env" code={`APIFY_API_TOKEN=your_apify_token\nANTHROPIC_API_KEY=your_anthropic_key\nSUPABASE_URL=https://your-project.supabase.co\nSUPABASE_KEY=your_service_role_key`} />
          <div className="space-y-1 text-sm" style={{ color: "#6b9b6b" }}>
            <div>• <strong style={{ color: "#f0faf0" }}>Apify</strong> — apify.com → Settings → Integrations → API tokens</div>
            <div>• <strong style={{ color: "#f0faf0" }}>Anthropic</strong> — console.anthropic.com → API Keys</div>
            <div>• <strong style={{ color: "#f0faf0" }}>Supabase URL + Key</strong> — Project Settings → API → use <strong>service_role</strong> key</div>
          </div>
        </Step>

        <Step number="4" title="Connect this dashboard to your pipeline">
          <P>The pipeline posts data to this dashboard's API. Add the dashboard URL to your pipeline's .env:</P>
          <CodeBlock lang=".env" code={`# Add to job-outreach/.env\nDASHBOARD_API_URL=https://your-deployed-dashboard.workers.dev`} />
          <P>Then in <code className="text-green-400">main.py</code>, the pipeline will POST results here after each run. Alternatively, import/export via CSV.</P>
        </Step>

        <Step number="5" title="Convert your resume (one time)">
          <CodeBlock lang="bash" code={`python utils/docx_converter.py your_resume.docx\n# → saves to data/master_resume.md`} />
          <P>Make sure your resume has a <strong style={{ color: "#f0faf0" }}>Summary</strong> or <strong style={{ color: "#f0faf0" }}>About</strong> section near the top — Claude uses this to personalise each outreach message.</P>
        </Step>

        <Step number="6" title="Run the pipeline">
          <CodeBlock lang="bash" code={`python main.py`} />
          <P>Expected output:</P>
          <CodeBlock lang="output" code={`09:01 | INFO | Pipeline started\n09:01 | INFO | Built 20 search URLs (5 titles × 4 locations)\n09:02 | INFO | Scraped 87 raw jobs\n09:02 | INFO | Accepted: 23 | Filtered: 64\n09:04 | INFO | Messages generated: 22\n09:04 | INFO | CSV exported: output/exports/outreach_2025-01-15.csv`} />
        </Step>

        <Step number="7" title="Set up cron (3× daily, every 5 hours)">
          <CodeBlock lang="bash" code={`crontab -e\n# Paste these 3 lines:`} />
          <CodeBlock lang="crontab" code={`0 9  * * *  cd /path/to/job-outreach && python3 main.py >> logs/cron.log 2>&1\n0 14 * * *  cd /path/to/job-outreach && python3 main.py >> logs/cron.log 2>&1\n0 19 * * *  cd /path/to/job-outreach && python3 main.py >> logs/cron.log 2>&1`} />
          <P>Each run fetches only jobs posted in the last 5 hours. No overlap between runs.</P>
        </Step>

        <Step number="8" title="Workflow: send messages manually">
          <div className="space-y-2 text-sm" style={{ color: "#6b9b6b" }}>
            <div className="flex gap-2">
              <span style={{ color: "#22c55e" }}>1.</span>
              Pipeline runs → jobs appear on Dashboard with status <span className="px-1 py-0.5 rounded text-xs" style={{ background: "#1e3a5f", color: "#60a5fa" }}>Ready</span>
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#22c55e" }}>2.</span>
              Go to <strong style={{ color: "#f0faf0" }}>All Jobs</strong> → expand a card → copy the outreach message
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#22c55e" }}>3.</span>
              Visit recruiter's LinkedIn URL → paste message → send
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#22c55e" }}>4.</span>
              Update status to <span className="px-1 py-0.5 rounded text-xs" style={{ background: "#3d2c00", color: "#fbbf24" }}>Sent</span> in the dashboard
            </div>
            <div className="flex gap-2">
              <span style={{ color: "#22c55e" }}>5.</span>
              Track replies → update to <span className="px-1 py-0.5 rounded text-xs" style={{ background: "#0d2e1a", color: "#22c55e" }}>Replied</span> or <span className="px-1 py-0.5 rounded text-xs" style={{ background: "#2d1b4e", color: "#c084fc" }}>Interview</span>
            </div>
          </div>
        </Step>

        {/* API reference */}
        <div
          className="rounded-xl border p-5 mt-6"
          style={{ background: "#111a11", borderColor: "#1e2e1e" }}
        >
          <div className="text-xs uppercase tracking-widest mb-4" style={{ color: "#6b9b6b", fontFamily: "JetBrains Mono, monospace" }}>
            API Endpoints (for pipeline integration)
          </div>
          <div className="space-y-2 text-xs" style={{ fontFamily: "JetBrains Mono, monospace" }}>
            {[
              ["POST", "/api/jobs", "Upsert job(s) from pipeline"],
              ["GET",  "/api/jobs", "List all jobs (supports ?status=&search=)"],
              ["PATCH","/api/jobs/:id/status", "Update job status"],
              ["GET",  "/api/stats", "Dashboard metrics"],
              ["POST", "/api/runs", "Log a pipeline run"],
              ["GET",  "/api/export/csv", "Download CSV of all jobs"],
            ].map(([method, path, desc]) => (
              <div key={path} className="flex items-start gap-3">
                <span
                  className="px-1.5 py-0.5 rounded text-xs flex-shrink-0"
                  style={{
                    background: method === "GET" ? "#0d2040" : method === "POST" ? "#0d2e1a" : "#3d2c00",
                    color: method === "GET" ? "#60a5fa" : method === "POST" ? "#22c55e" : "#fbbf24",
                  }}
                >
                  {method}
                </span>
                <span style={{ color: "#d1fae5" }}>{path}</span>
                <span style={{ color: "#3d6b3d" }}>{desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
