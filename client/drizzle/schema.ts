import { pgTable, index, foreignKey, check, uuid, text, timestamp, integer, varchar, boolean, jsonb, numeric, date, unique, bigint, serial, primaryKey, pgSequence } from "drizzle-orm/pg-core"
import { sql } from "drizzle-orm"


export const krxDetailIdSeq = pgSequence("krx_detail_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const marketTickersIdSeq = pgSequence("market_tickers_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krPriceIdSeq = pgSequence("kr_price_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krPriceSubIdSeq = pgSequence("kr_price_sub_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krTotalIdSeq = pgSequence("kr_total_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const usTestIdSeq = pgSequence("us_test_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krxBasicIdSeq = pgSequence("krx_basic_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const jobStatusIdSeq = pgSequence("job_status_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const chatMessageLogsIdSeq = pgSequence("chat_message_logs_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "9223372036854775807", cache: "1", cycle: false })
export const krAnnounceIdSeq = pgSequence("kr_announce_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krDocumentRawContentIdSeq = pgSequence("kr_document_raw_content_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krDocumentStructuredIdSeq = pgSequence("kr_document_structured_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krAnnounceProgressIdSeq = pgSequence("kr_announce_progress_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krAuditIdSeq = pgSequence("kr_audit_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krDividendsIdSeq = pgSequence("kr_dividends_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krLargestShareholderIdSeq = pgSequence("kr_largest_shareholder_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krStockacquisitiondisposalIdSeq = pgSequence("kr_stockacquisitiondisposal_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const usBbandsIdSeq = pgSequence("us_bbands_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const reportReportIdSeq = pgSequence("report_report_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const reportPagePageIdSeq = pgSequence("report_page_page_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const aiAccountMappingIdSeq = pgSequence("ai_account_mapping_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const aiQueryTemplatesIdSeq = pgSequence("ai_query_templates_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const aiQueryUsageLogIdSeq = pgSequence("ai_query_usage_log_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const aiQueryLogIdSeq = pgSequence("ai_query_log_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const usDailyEtfIdSeq = pgSequence("us_daily_etf_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krHistoricalPatternsPatternIdSeq = pgSequence("kr_historical_patterns_pattern_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krPatternStatisticsStatIdSeq = pgSequence("kr_pattern_statistics_stat_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })
export const krSectorReturnHistoryHistoryIdSeq = pgSequence("kr_sector_return_history_history_id_seq", {  startWith: "1", increment: "1", minValue: "1", maxValue: "2147483647", cache: "1", cycle: false })

export const chatSessions = pgTable("chat_sessions", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	userId: uuid("user_id").notNull(),
	title: text().notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).defaultNow().notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'date' }).defaultNow().notNull(),
	messageCount: integer("message_count").default(0).notNull(),
	modelId: varchar("model_id", { length: 50 }).default('stock-ai').notNull(),
	isArchived: boolean("is_archived").default(false),
	isPinned: boolean("is_pinned").default(false),
	llmProvider: varchar("llm_provider", { length: 50 }).default('anthropic'),
	llmModel: varchar("llm_model", { length: 100 }).default('claude-sonnet-4-20250514'),
	lastMessageAt: timestamp("last_message_at", { mode: 'date' }),
	chatServiceType: varchar("chat_service_type", { length: 50 }).default('ALPHA'),
}, (table) => [
	index("idx_chat_sessions_updated").using("btree", table.updatedAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_chat_sessions_user_created").using("btree", table.userId.asc().nullsLast().op("uuid_ops"), table.createdAt.desc().nullsFirst().op("uuid_ops")),
	index("idx_chat_sessions_user_model").using("btree", table.userId.asc().nullsLast().op("timestamptz_ops"), table.modelId.asc().nullsLast().op("uuid_ops"), table.updatedAt.desc().nullsFirst().op("text_ops")),
	index("idx_chat_sessions_user_updated").using("btree", table.userId.asc().nullsLast().op("uuid_ops"), table.updatedAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_user_archived").using("btree", table.userId.asc().nullsLast().op("uuid_ops"), table.isArchived.asc().nullsLast().op("uuid_ops"), table.updatedAt.desc().nullsFirst().op("uuid_ops")),
	index("idx_user_updated").using("btree", table.userId.asc().nullsLast().op("uuid_ops"), table.updatedAt.desc().nullsFirst().op("uuid_ops")),
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "fk_chat_sessions_user_id"
		}).onDelete("cascade"),
	check("chk_message_count", sql`message_count >= 0`),
	check("chk_title_length", sql`(length(TRIM(BOTH FROM title)) >= 1) AND (length(title) <= 200)`),
]);

export const chatMessages = pgTable("chat_messages", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	sessionId: uuid("session_id").notNull(),
	role: text().notNull(),
	content: text().notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).defaultNow().notNull(),
	tokensUsed: integer("tokens_used"),
	modelUsed: varchar("model_used", { length: 100 }),
	toolsUsed: jsonb("tools_used"),
	processingTimeMs: integer("processing_time_ms"),
}, (table) => [
	index("idx_chat_messages_created").using("btree", table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_chat_messages_session_created").using("btree", table.sessionId.asc().nullsLast().op("uuid_ops"), table.createdAt.asc().nullsLast().op("uuid_ops")),
	index("idx_chat_messages_user_search").using("btree", table.sessionId.asc().nullsLast().op("uuid_ops"), table.role.asc().nullsLast().op("uuid_ops"), table.content.asc().nullsLast().op("uuid_ops"), table.createdAt.asc().nullsLast().op("uuid_ops")),
	foreignKey({
			columns: [table.sessionId],
			foreignColumns: [chatSessions.id],
			name: "fk_chat_messages_session_id"
		}).onDelete("cascade"),
	check("chk_content_not_empty", sql`length(TRIM(BOTH FROM content)) > 0`),
	check("chk_role_valid", sql`role = ANY (ARRAY['user'::text, 'assistant'::text])`),
]);

export const futureKr = pgTable("future_kr", {
	tickerSymbol: text("ticker_symbol").primaryKey().notNull(),
	countryCode: text("country_code"),
	stockName: text("stock_name"),
	stockEngName: text("stock_eng_name"),
	marketName: text("market_name"),
	currentPrice: numeric("current_price", { precision: 19, scale:  2 }),
	changePercent: numeric("change_percent", { precision: 10, scale:  2 }),
	futurePrice: numeric("future_price", { precision: 19, scale:  2 }),
	futureEarnings: numeric("future_earnings", { precision: 19, scale:  2 }),
	futurePercent: numeric("future_percent", { precision: 10, scale:  2 }),
	insight: text(),
	url1: text("url_1"),
	url2: text("url_2"),
	url3: text("url_3"),
	url4: text("url_4"),
	url5: text("url_5"),
	recordUpdatedAt: timestamp("record_updated_at", { withTimezone: true, mode: 'date' }),
	title1: text(),
	content1: text(),
	title2: text(),
	content2: text(),
	title3: text(),
	content3: text(),
	title4: text(),
	content4: text(),
	title5: text(),
	content5: text(),
	industryName: varchar("industry_name", { length: 255 }),
});

export const todayKr = pgTable("today_kr", {
	tickerSymbol: text("ticker_symbol").primaryKey().notNull(),
	countryCode: text("country_code"),
	stockName: text("stock_name"),
	stockEngName: text("stock_eng_name"),
	marketName: text("market_name"),
	currentPrice: numeric("current_price", { precision: 19, scale:  2 }),
	changePercent: numeric("change_percent", { precision: 10, scale:  2 }),
	futurePrice: numeric("future_price", { precision: 19, scale:  2 }),
	futureEarnings: numeric("future_earnings", { precision: 19, scale:  2 }),
	futurePercent: numeric("future_percent", { precision: 10, scale:  2 }),
	insight: text(),
	url1: text("url_1"),
	url2: text("url_2"),
	url3: text("url_3"),
	url4: text("url_4"),
	url5: text("url_5"),
	recordUpdatedAt: timestamp("record_updated_at", { withTimezone: true, mode: 'date' }),
	title1: text(),
	content1: text(),
	title2: text(),
	content2: text(),
	title3: text(),
	content3: text(),
	title4: text(),
	content4: text(),
	title5: text(),
	content5: text(),
	industryName: varchar("industry_name", { length: 255 }),
});

export const shareActivityLogs = pgTable("share_activity_logs", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	userId: uuid("user_id"),
	pageType: varchar("page_type", { length: 20 }).notNull(),
	countryCode: varchar("country_code", { length: 2 }).notNull(),
	userAgent: text("user_agent"),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
}, (table) => [
	index("idx_share_activity_logs_created").using("btree", table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_share_activity_logs_page_country").using("btree", table.pageType.asc().nullsLast().op("text_ops"), table.countryCode.asc().nullsLast().op("timestamptz_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_share_activity_logs_user_created").using("btree", table.userId.asc().nullsLast().op("uuid_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")).where(sql`(user_id IS NOT NULL)`),
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "fk_share_activity_logs_user_id"
		}).onDelete("set null"),
	check("chk_share_activity_country_code", sql`(country_code)::text = ANY ((ARRAY['KR'::character varying, 'US'::character varying])::text[])`),
	check("chk_share_activity_page_type", sql`(page_type)::text = ANY ((ARRAY['today'::character varying, 'future'::character varying])::text[])`),
]);

export const userStatistics = pgTable("user_statistics", {
	statDate: date("stat_date").primaryKey().notNull(),
	dailySignupCount: integer("daily_signup_count").default(0).notNull(),
	totalSignupCount: integer("total_signup_count").default(0).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
}, (table) => [
	index("idx_user_statistics_date_desc").using("btree", table.statDate.desc().nullsFirst().op("date_ops")),
	check("chk_user_statistics_counts", sql`(daily_signup_count >= 0) AND (total_signup_count >= 0)`),
]);

export const userLimits = pgTable("user_limits", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	userId: uuid("user_id").notNull(),
	dailyChatLimit: integer("daily_chat_limit").default(5).notNull(),
	limitType: varchar("limit_type", { length: 50 }).default('standard'),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
}, (table) => [
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "user_limits_user_id_fkey"
		}).onDelete("cascade"),
	unique("user_limits_user_id_key").on(table.userId),
]);

export const signupActivityLogs = pgTable("signup_activity_logs", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	userId: uuid("user_id").notNull(),
	actionType: varchar("action_type", { length: 20 }).notNull(),
	utmSource: varchar("utm_source", { length: 50 }),
	utmMedium: varchar("utm_medium", { length: 50 }),
	utmCampaign: varchar("utm_campaign", { length: 50 }),
	utmContent: varchar("utm_content", { length: 50 }),
	userAgent: text("user_agent"),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
}, (table) => [
	index("idx_signup_activity_logs_created").using("btree", table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_signup_activity_logs_user_created").using("btree", table.userId.asc().nullsLast().op("timestamptz_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_signup_activity_logs_utm").using("btree", table.utmSource.asc().nullsLast().op("text_ops"), table.utmMedium.asc().nullsLast().op("text_ops"), table.utmCampaign.asc().nullsLast().op("text_ops")),
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "signup_activity_logs_user_id_fkey"
		}).onDelete("cascade"),
	check("signup_activity_logs_action_type_check", sql`(action_type)::text = ANY (ARRAY[('signup'::character varying)::text, ('login'::character varying)::text, ('restore'::character varying)::text])`),
]);

export const todayUs = pgTable("today_us", {
	tickerSymbol: varchar("ticker_symbol", { length: 20 }).primaryKey().notNull(),
	stockName: varchar("stock_name", { length: 255 }),
	exchangeCode: varchar("exchange_code", { length: 50 }),
	open: numeric({ precision: 19, scale:  4 }),
	currentPrice: numeric("current_price", { precision: 19, scale:  4 }),
	changePercent: numeric("change_percent", { precision: 10, scale:  2 }),
	futurePrice: numeric("future_price", { precision: 19, scale:  4 }),
	futureEarnings: numeric("future_earnings", { precision: 19, scale:  4 }),
	futurePercent: numeric("future_percent", { precision: 10, scale:  2 }),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	value: bigint({ mode: "number" }),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	marketCap: bigint("market_cap", { mode: "number" }),
	insight: text(),
	url1: text("url_1"),
	title1: text(),
	content1: text(),
	url2: text("url_2"),
	title2: text(),
	content2: text(),
	url3: text("url_3"),
	title3: text(),
	content3: text(),
	url4: text("url_4"),
	title4: text(),
	content4: text(),
	url5: text("url_5"),
	title5: text(),
	content5: text(),
	recordUpdatedAt: timestamp("record_updated_at", { mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	market: varchar({ length: 50 }),
});

export const futureUs = pgTable("future_us", {
	tickerSymbol: varchar("ticker_symbol", { length: 20 }).primaryKey().notNull(),
	stockName: varchar("stock_name", { length: 255 }),
	exchangeCode: varchar("exchange_code", { length: 50 }),
	open: numeric({ precision: 19, scale:  4 }),
	currentPrice: numeric("current_price", { precision: 19, scale:  4 }),
	changePercent: numeric("change_percent", { precision: 10, scale:  2 }),
	futurePrice: numeric("future_price", { precision: 19, scale:  4 }),
	futureEarnings: numeric("future_earnings", { precision: 19, scale:  4 }),
	futurePercent: numeric("future_percent", { precision: 10, scale:  2 }),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	value: bigint({ mode: "number" }),
	// You can use { mode: "bigint" } if numbers are exceeding js number limitations
	marketCap: bigint("market_cap", { mode: "number" }),
	insight: text(),
	url1: text("url_1"),
	title1: text(),
	content1: text(),
	url2: text("url_2"),
	title2: text(),
	content2: text(),
	url3: text("url_3"),
	title3: text(),
	content3: text(),
	url4: text("url_4"),
	title4: text(),
	content4: text(),
	url5: text("url_5"),
	title5: text(),
	content5: text(),
	recordUpdatedAt: timestamp("record_updated_at", { mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	market: varchar({ length: 50 }),
});

export const sessions = pgTable("sessions", {
	id: text().primaryKey().notNull(),
	userId: uuid("user_id").notNull(),
	expiresAt: timestamp("expires_at", { withTimezone: true, mode: 'date' }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	userAgent: text("user_agent"),
	ipAddress: varchar("ip_address", { length: 45 }),
	lastActivityAt: timestamp("last_activity_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
}, (table) => [
	index("idx_sessions_expires_at").using("btree", table.expiresAt.asc().nullsLast().op("timestamptz_ops")),
	index("idx_sessions_last_activity_at").using("btree", table.lastActivityAt.asc().nullsLast().op("timestamptz_ops")),
	index("idx_sessions_user_id").using("btree", table.userId.asc().nullsLast().op("uuid_ops")),
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "sessions_user_id_fkey"
		}).onDelete("cascade"),
]);

export const users = pgTable("users", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	oauthProvider: varchar("oauth_provider", { length: 50 }),
	oauthId: varchar("oauth_id", { length: 255 }),
	nickname: varchar({ length: 100 }),
	email: varchar({ length: 255 }).notNull(),
	gender: varchar({ length: 10 }),
	ageRange: varchar("age_range", { length: 10 }),
	profileImageUrl: varchar("profile_image_url", { length: 500 }),
	thumbnailImageUrl: varchar("thumbnail_image_url", { length: 500 }),
	hasCompletedOnboarding: boolean("has_completed_onboarding").default(false),
	lastLoginAt: timestamp("last_login_at", { withTimezone: true, mode: 'date' }),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`),
	isActive: boolean("is_active").default(true),
	deletedAt: timestamp("deleted_at", { withTimezone: true, mode: 'date' }),
}, (table) => [
	index("idx_users_deleted_at").using("btree", table.deletedAt.asc().nullsLast().op("timestamptz_ops")),
	index("idx_users_email_active").using("btree", table.email.asc().nullsLast().op("text_ops"), table.deletedAt.asc().nullsLast().op("text_ops")),
	index("idx_users_oauth_active").using("btree", table.oauthProvider.asc().nullsLast().op("timestamptz_ops"), table.oauthId.asc().nullsLast().op("text_ops"), table.deletedAt.asc().nullsLast().op("timestamptz_ops")),
	unique("uq_users_oauth").on(table.oauthProvider, table.oauthId),
	unique("uq_users_email").on(table.email),
]);

export const dailyUserRetention = pgTable("daily_user_retention", {
	id: serial().primaryKey().notNull(),
	userId: varchar("user_id", { length: 255 }).notNull(),
	activityDate: date("activity_date").notNull(),
	entryPage: varchar("entry_page", { length: 100 }),
	visitTime: timestamp("visit_time", { mode: 'date' }).defaultNow(),
	createdAt: timestamp("created_at", { mode: 'date' }).defaultNow(),
	updatedAt: timestamp("updated_at", { mode: 'date' }).defaultNow(),
}, (table) => [
	index("idx_retention_date").using("btree", table.activityDate.asc().nullsLast().op("date_ops")),
	index("idx_retention_user").using("btree", table.userId.asc().nullsLast().op("text_ops")),
	index("idx_retention_user_date").using("btree", table.userId.asc().nullsLast().op("text_ops"), table.activityDate.asc().nullsLast().op("date_ops")),
	unique("daily_user_retention_user_id_activity_date_key").on(table.userId, table.activityDate),
]);

export const favorites = pgTable("favorites", {
	id: uuid().defaultRandom().primaryKey().notNull(),
	userId: uuid("user_id").notNull(),
	itemType: varchar("item_type", { length: 20 }).notNull(),
	itemId: varchar("item_id", { length: 100 }).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
}, (table) => [
	index("idx_favorites_item").using("btree", table.itemType.asc().nullsLast().op("text_ops"), table.itemId.asc().nullsLast().op("text_ops")),
	index("idx_favorites_user_created").using("btree", table.userId.asc().nullsLast().op("timestamptz_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	index("idx_favorites_user_type").using("btree", table.userId.asc().nullsLast().op("text_ops"), table.itemType.asc().nullsLast().op("uuid_ops"), table.createdAt.desc().nullsFirst().op("timestamptz_ops")),
	foreignKey({
			columns: [table.userId],
			foreignColumns: [users.id],
			name: "fk_favorites_user_id"
		}).onDelete("cascade"),
	unique("uq_favorites_user_item").on(table.userId, table.itemType, table.itemId),
	check("chk_favorites_item_type", sql`(item_type)::text = ANY ((ARRAY['PORTFOLIO'::character varying, 'STOCK'::character varying])::text[])`),
]);

export const shareStatistics = pgTable("share_statistics", {
	statDate: date("stat_date").notNull(),
	pageType: varchar("page_type", { length: 20 }).notNull(),
	countryCode: varchar("country_code", { length: 2 }).notNull(),
	dailyShareCount: integer("daily_share_count").default(0).notNull(),
	totalShareCount: integer("total_share_count").default(0).notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'date' }).default(sql`CURRENT_TIMESTAMP`).notNull(),
}, (table) => [
	index("idx_share_statistics_date_desc").using("btree", table.statDate.desc().nullsFirst().op("date_ops")),
	index("idx_share_statistics_page_country").using("btree", table.pageType.asc().nullsLast().op("text_ops"), table.countryCode.asc().nullsLast().op("text_ops"), table.statDate.desc().nullsFirst().op("text_ops")),
	primaryKey({ columns: [table.statDate, table.pageType, table.countryCode], name: "share_statistics_pkey"}),
	check("chk_share_statistics_country_code", sql`(country_code)::text = ANY ((ARRAY['KR'::character varying, 'US'::character varying])::text[])`),
	check("chk_share_statistics_counts", sql`(daily_share_count >= 0) AND (total_share_count >= 0)`),
	check("chk_share_statistics_page_type", sql`(page_type)::text = ANY ((ARRAY['today'::character varying, 'future'::character varying])::text[])`),
]);
