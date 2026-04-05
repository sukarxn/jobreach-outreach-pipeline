import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const jobs = sqliteTable("jobs", {
  id: text("id").primaryKey(),
  jobUrl: text("job_url").notNull().unique(),
  jobTitle: text("job_title"),
  companyName: text("company_name"),
  location: text("location"),
  postedAt: text("posted_at"),
  descriptionText: text("description_text"),
  seniorityLevel: text("seniority_level"),
  employmentType: text("employment_type"),
  applyUrl: text("apply_url"),
  applicantsCount: text("applicants_count"),

  // Recruiter
  recruiterName: text("recruiter_name"),
  recruiterTitle: text("recruiter_title"),
  recruiterPhoto: text("recruiter_photo"),
  recruiterLinkedin: text("recruiter_linkedin"),

  // Outreach
  outreachMessage: text("outreach_message"),
  messageStatus: text("message_status").default("pending"),

  // Meta
  scrapedAt: text("scraped_at").default(sql`(datetime('now'))`),
  exportedAt: text("exported_at"),
  notes: text("notes"),
});

export const pipelineRuns = sqliteTable("pipeline_runs", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  runAt: text("run_at").default(sql`(datetime('now'))`),
  status: text("status").default("running"), // running | completed | failed
  jobsScraped: integer("jobs_scraped").default(0),
  jobsAccepted: integer("jobs_accepted").default(0),
  messagesGenerated: integer("messages_generated").default(0),
  durationSeconds: integer("duration_seconds"),
  errorMessage: text("error_message"),
});
