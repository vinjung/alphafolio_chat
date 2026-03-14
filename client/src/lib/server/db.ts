import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from '@schema';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

// 글로벌 싱글톤 안전 패턴
const globalForDb = globalThis as unknown as {
  db?: PostgresJsDatabase<typeof schema>;
};

let db: PostgresJsDatabase<typeof schema>;

if (process.env.NODE_ENV === 'production') {
  db = drizzle(postgres(process.env.DATABASE_URL!), { schema });
} else {
  if (!globalForDb.db) {
    globalForDb.db = drizzle(postgres(process.env.DATABASE_PUBLIC_URL!), { schema });
  }
  db = globalForDb.db;
}

export { db };
