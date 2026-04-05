import { Hono } from "hono";
import { drizzle } from "drizzle-orm/d1";
import { jobs, pipelineRuns } from "./database/schema";
import { eq, desc, like, or, and, count } from "drizzle-orm";

type Bindings = { DB: D1Database };
const app = new Hono<{ Bindings: Bindings }>();

// ── Jobs CRUD ─────────────────────────────────────────────────────────────────

// GET /api/jobs — list all jobs with optional filters
app.get("/api/jobs", async (c) => {
  const db = drizzle(c.env.DB);
  const { status, search, limit = "200" } = c.req.query();

  try {
    const conditions = [];
    if (status && status !== "all") conditions.push(eq(jobs.messageStatus, status));
    if (search) {
      conditions.push(
        or(
          like(jobs.jobTitle, `%${search}%`),
          like(jobs.companyName, `%${search}%`),
          like(jobs.recruiterName, `%${search}%`)
        )
      );
    }

    const query = db
      .select()
      .from(jobs)
      .orderBy(desc(jobs.scrapedAt))
      .limit(parseInt(limit));

    const result = conditions.length > 0
      ? await query.where(conditions.length === 1 ? conditions[0] : and(...conditions))
      : await query;

    return c.json({ jobs: result });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// POST /api/jobs — upsert a job (from Python pipeline)
app.post("/api/jobs", async (c) => {
  const db = drizzle(c.env.DB);
  try {
    const body = await c.req.json();
    const jobData = Array.isArray(body) ? body : [body];

    for (const job of jobData) {
      await db.insert(jobs).values({
        id: job.id,
        jobUrl: job.job_url,
        jobTitle: job.job_title,
        companyName: job.company_name,
        location: job.location,
        postedAt: job.posted_at,
        descriptionText: job.description_text,
        seniorityLevel: job.seniority_level,
        employmentType: job.employment_type,
        applyUrl: job.apply_url,
        applicantsCount: job.applicants_count,
        recruiterName: job.recruiter_name,
        recruiterTitle: job.recruiter_title,
        recruiterPhoto: job.recruiter_photo,
        recruiterLinkedin: job.recruiter_linkedin,
        outreachMessage: job.outreach_message,
        messageStatus: job.message_status || "pending",
        notes: job.notes,
      }).onConflictDoUpdate({
        target: jobs.id,
        set: {
          outreachMessage: job.outreach_message,
          messageStatus: job.message_status,
          recruiterName: job.recruiter_name,
          recruiterTitle: job.recruiter_title,
          recruiterLinkedin: job.recruiter_linkedin,
          notes: job.notes,
        },
      });
    }
    return c.json({ ok: true, count: jobData.length });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// PATCH /api/jobs/:id/status — update status from dashboard
app.patch("/api/jobs/:id/status", async (c) => {
  const db = drizzle(c.env.DB);
  const { id } = c.req.param();
  try {
    const { status, notes } = await c.req.json();
    const updateData: Record<string, string> = { messageStatus: status };
    if (notes !== undefined) updateData.notes = notes;
    await db.update(jobs).set(updateData).where(eq(jobs.id, id));
    return c.json({ ok: true });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// DELETE /api/jobs/:id
app.delete("/api/jobs/:id", async (c) => {
  const db = drizzle(c.env.DB);
  const { id } = c.req.param();
  try {
    await db.delete(jobs).where(eq(jobs.id, id));
    return c.json({ ok: true });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// ── Stats ─────────────────────────────────────────────────────────────────────

app.get("/api/stats", async (c) => {
  const db = drizzle(c.env.DB);
  try {
    const allJobs = await db.select().from(jobs).all();
    const today = new Date().toISOString().slice(0, 10);
    const todayJobs = allJobs.filter(j => (j.scrapedAt || "").startsWith(today));

    const stats = {
      total: allJobs.length,
      todayScraped: todayJobs.length,
      messagesGenerated: allJobs.filter(j => j.messageStatus === "message_generated").length,
      sentManually: allJobs.filter(j => j.messageStatus === "sent_manually").length,
      replied: allJobs.filter(j => j.messageStatus === "replied").length,
      noReply: allJobs.filter(j => j.messageStatus === "no_reply").length,
      interview: allJobs.filter(j => j.messageStatus === "interview").length,
      filteredOut: allJobs.filter(j => j.messageStatus === "filtered_out").length,
    };
    return c.json(stats);
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// ── Pipeline Runs ─────────────────────────────────────────────────────────────

app.get("/api/runs", async (c) => {
  const db = drizzle(c.env.DB);
  try {
    const runs = await db.select().from(pipelineRuns).orderBy(desc(pipelineRuns.runAt)).limit(20);
    return c.json({ runs });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

app.post("/api/runs", async (c) => {
  const db = drizzle(c.env.DB);
  try {
    const body = await c.req.json();
    const [run] = await db.insert(pipelineRuns).values({
      status: body.status || "completed",
      jobsScraped: body.jobs_scraped || 0,
      jobsAccepted: body.jobs_accepted || 0,
      messagesGenerated: body.messages_generated || 0,
      durationSeconds: body.duration_seconds,
      errorMessage: body.error_message,
    }).returning();
    return c.json({ run });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

// ── CSV Export ────────────────────────────────────────────────────────────────

app.get("/api/export/csv", async (c) => {
  const db = drizzle(c.env.DB);
  try {
    const allJobs = await db.select().from(jobs).orderBy(desc(jobs.scrapedAt)).all();

    const headers = [
      "id", "job_title", "company_name", "location", "posted_at",
      "job_url", "apply_url", "recruiter_name", "recruiter_title",
      "recruiter_linkedin", "outreach_message", "message_status", "scraped_at", "notes"
    ];

    const escape = (val: any) => {
      if (val == null) return "";
      const str = String(val);
      if (str.includes(",") || str.includes('"') || str.includes("\n")) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    const rows = allJobs.map(j => [
      j.id, j.jobTitle, j.companyName, j.location, j.postedAt,
      j.jobUrl, j.applyUrl, j.recruiterName, j.recruiterTitle,
      j.recruiterLinkedin, j.outreachMessage, j.messageStatus, j.scrapedAt, j.notes
    ].map(escape).join(","));

    const csv = [headers.join(","), ...rows].join("\n");
    const date = new Date().toISOString().slice(0, 10);

    return new Response(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="outreach_${date}.csv"`,
      },
    });
  } catch (e: any) {
    return c.json({ error: e.message }, 500);
  }
});

export default app;
