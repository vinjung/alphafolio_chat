-- Current sql file was generated after introspecting the database
-- If you want to run this migration please uncomment this code before executing migrations
/*
CREATE TABLE "users" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"oauth_provider" varchar(50),
	"oauth_id" varchar(255),
	"nickname" varchar(100),
	"email" varchar(255) NOT NULL,
	"phone_number" varchar(20) NOT NULL,
	"gender" varchar(10),
	"age_range" varchar(10),
	"profile_image_url" varchar(500),
	"last_login_at" timestamp with time zone,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
	"updated_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
	"is_active" boolean DEFAULT true,
	CONSTRAINT "uq_users_oauth" UNIQUE("oauth_provider","oauth_id"),
	CONSTRAINT "uq_users_email" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "sessions" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" uuid NOT NULL,
	"expires_at" timestamp with time zone NOT NULL,
	"created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
	"user_agent" text,
	"ip_address" varchar(45),
	"last_activity_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
--> statement-breakpoint
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_sessions_expires_at" ON "sessions" USING btree ("expires_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "idx_sessions_last_activity_at" ON "sessions" USING btree ("last_activity_at" timestamptz_ops);--> statement-breakpoint
CREATE INDEX "idx_sessions_user_id" ON "sessions" USING btree ("user_id" uuid_ops);
*/