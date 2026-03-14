import type { Config } from 'drizzle-kit';
import * as dotenv from 'dotenv';
dotenv.config();

export default {
  out: './drizzle',
  dialect: 'postgresql',
  schema: './drizzle/schema.ts',
  dbCredentials: {
    // url: process.env.DATABASE_URL!,
    url: process.env.DATABASE_PUBLIC_URL!,
  },
  tablesFilter: [
    'users',
    'sessions',
    'today_kr',
    'future_kr',
    'today_us',
    'future_us',
    'chat_sessions',
    'chat_messages',
    'user_limits',
    'share_activity_logs',
    'signup_activity_logs',
    'user_statistics',
    'share_statistics',
    'daily_user_retention',
    'favorites',
  ],
} satisfies Config;
