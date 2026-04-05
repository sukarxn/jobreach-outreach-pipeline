CREATE TABLE `jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`job_url` text NOT NULL,
	`job_title` text,
	`company_name` text,
	`location` text,
	`posted_at` text,
	`description_text` text,
	`seniority_level` text,
	`employment_type` text,
	`apply_url` text,
	`applicants_count` text,
	`recruiter_name` text,
	`recruiter_title` text,
	`recruiter_photo` text,
	`recruiter_linkedin` text,
	`outreach_message` text,
	`message_status` text DEFAULT 'pending',
	`scraped_at` text DEFAULT (datetime('now')),
	`exported_at` text,
	`notes` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX `jobs_job_url_unique` ON `jobs` (`job_url`);--> statement-breakpoint
CREATE TABLE `pipeline_runs` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`run_at` text DEFAULT (datetime('now')),
	`status` text DEFAULT 'running',
	`jobs_scraped` integer DEFAULT 0,
	`jobs_accepted` integer DEFAULT 0,
	`messages_generated` integer DEFAULT 0,
	`duration_seconds` integer,
	`error_message` text
);
