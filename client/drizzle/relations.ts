import { relations } from "drizzle-orm/relations";
import { users, chatSessions, chatMessages, shareActivityLogs, userLimits, signupActivityLogs, sessions, favorites } from "./schema";

export const chatSessionsRelations = relations(chatSessions, ({one, many}) => ({
	user: one(users, {
		fields: [chatSessions.userId],
		references: [users.id]
	}),
	chatMessages: many(chatMessages),
}));

export const usersRelations = relations(users, ({many}) => ({
	chatSessions: many(chatSessions),
	shareActivityLogs: many(shareActivityLogs),
	userLimits: many(userLimits),
	signupActivityLogs: many(signupActivityLogs),
	sessions: many(sessions),
	favorites: many(favorites),
}));

export const chatMessagesRelations = relations(chatMessages, ({one}) => ({
	chatSession: one(chatSessions, {
		fields: [chatMessages.sessionId],
		references: [chatSessions.id]
	}),
}));

export const shareActivityLogsRelations = relations(shareActivityLogs, ({one}) => ({
	user: one(users, {
		fields: [shareActivityLogs.userId],
		references: [users.id]
	}),
}));

export const userLimitsRelations = relations(userLimits, ({one}) => ({
	user: one(users, {
		fields: [userLimits.userId],
		references: [users.id]
	}),
}));

export const signupActivityLogsRelations = relations(signupActivityLogs, ({one}) => ({
	user: one(users, {
		fields: [signupActivityLogs.userId],
		references: [users.id]
	}),
}));

export const sessionsRelations = relations(sessions, ({one}) => ({
	user: one(users, {
		fields: [sessions.userId],
		references: [users.id]
	}),
}));

export const favoritesRelations = relations(favorites, ({one}) => ({
	user: one(users, {
		fields: [favorites.userId],
		references: [users.id]
	}),
}));