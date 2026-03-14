import {
  users,
  sessions,
  chatSessions,
  chatMessages,
  shareActivityLogs,
  userStatistics,
  shareStatistics,
  signupActivityLogs,
  dailyUserRetention,
} from '@schema';
import { InferInsertModel, InferSelectModel } from 'drizzle-orm';

// Drizzle kit pull 이후에 테이블 추가되는경우 본 파일에 추가로 추론 타입 추가해줘야함...

export type User = InferSelectModel<typeof users>;
export type NewUser = InferInsertModel<typeof users>;
export type Session = InferSelectModel<typeof sessions>;
export type NewSession = InferInsertModel<typeof sessions>;

export type ChatSession = InferSelectModel<typeof chatSessions>;
export type NewChatSession = InferInsertModel<typeof chatSessions>;
export type ChatMessage = InferSelectModel<typeof chatMessages>;
export type NewChatMessage = InferInsertModel<typeof chatMessages>;

export type ShareActivityLog = InferSelectModel<typeof shareActivityLogs>;
export type NewShareActivityLog = InferInsertModel<typeof shareActivityLogs>;

export type UserStatistics = InferSelectModel<typeof userStatistics>;
export type NewUserStatistics = InferInsertModel<typeof userStatistics>;

export type ShareStatistics = InferSelectModel<typeof shareStatistics>;
export type NewShareStatistics = InferInsertModel<typeof shareStatistics>;

export type SignupActivityLog = InferSelectModel<typeof signupActivityLogs>;
export type NewSignupActivityLog = InferInsertModel<typeof signupActivityLogs>;

export type DailyUserRetention = InferSelectModel<typeof dailyUserRetention>;
export type NewDailyUserRetention = InferInsertModel<typeof dailyUserRetention>;
