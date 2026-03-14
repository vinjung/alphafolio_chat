import type { User, Session, NewSession } from './models.js';
import { db } from './db';
import { eq, and, isNull } from 'drizzle-orm';
import {
  encodeBase32LowerCaseNoPadding,
  encodeHexLowerCase,
} from '@oslojs/encoding';
import { sha256 } from '@oslojs/crypto/sha2';
import { users as userTable, sessions as sessionTable } from '@schema';
import { cache } from 'react';
import { cookies } from 'next/headers.js';

/**
 * 패딩 없는 소문자 Base32 형식의 보안 세션 토큰을 생성합니다.
 *
 * @returns {string} 암호학적으로 안전한 세션 토큰 문자열 (소문자 Base32 인코딩).
 *
 * @example
 * const token = generateSessionToken();
 * console.log(token); // 예: 'mzxw6ytboi2gk3t5h7q8'
 */
export function generateSessionToken(): string {
  const bytes = new Uint8Array(20);
  crypto.getRandomValues(bytes);
  const token = encodeBase32LowerCaseNoPadding(bytes);
  return token;
}

/**
 * 주어진 토큰과 사용자 ID를 기반으로 새로운 세션을 생성하고 DB에 저장합니다.
 *
 * 세션 ID는 토큰을 SHA-256으로 해싱 후, 소문자 hex로 인코딩하여 생성되며,
 * 세션 만료 시간은 현재 시각 기준 30일 후로 설정됩니다.
 *
 * @param {string} token - 세션을 식별하기 위한 원본 토큰 문자열
 * @param {string} userId - 세션과 연결할 사용자 UUID
 * @returns {Promise<NewSession>} 생성된 세션 객체를 반환합니다
 *
 * @example
 * const token = generateSessionToken();
 * const session = await createSession(token, user.id);
 * console.log(session.id); // 해싱된 세션 ID
 */
export async function createSession(
  token: string,
  userId: string
): Promise<NewSession> {
  const sessionId = encodeHexLowerCase(sha256(new TextEncoder().encode(token)));

  const session: NewSession = {
    id: sessionId,
    userId,
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30),
  };

  await db.insert(sessionTable).values(session);
  return session;
}

/**
 * 주어진 세션 토큰을 검증하고 유효한 경우 사용자와 세션 정보를 반환합니다.
 * ✅ 삭제된 사용자(deleted_at이 NULL이 아닌 경우)의 세션은 무효화됩니다.
 *
 * 이 함수는 다음과 같은 단계를 수행합니다:
 * 1. 토큰을 SHA-256 해싱 후, 세션 ID로 변환합니다.
 * 2. 세션 ID와 매칭되는 세션 + 사용자 정보를 DB에서 조회합니다.
 * 3. 세션이 존재하지 않거나, 이미 만료되었으면 삭제 후 null 반환합니다.
 * 4. 세션 만료까지 15일 이하로 남았다면 만료 시간을 30일 뒤로 갱신합니다.
 * 5. 유효한 경우 세션과 사용자 정보를 함께 반환합니다.
 *
 * @param {string} token - 확인하고자 하는 원본 세션 토큰
 * @returns {Promise<SessionValidationResult>}
 *          유효한 경우 `{ session, user }`,
 *          유효하지 않은 경우 `{ session: null, user: null }` 형태 반환
 *
 * @example
 * const result = await validateSessionToken(token);
 * if (result.session) {
 *   console.log("유효한 세션입니다:", result.user);
 * } else {
 *   console.log("세션이 만료되었거나 존재하지 않습니다.");
 * }
 */
export async function validateSessionToken(
  token: string
): Promise<SessionValidationResult> {
  const sessionId = encodeHexLowerCase(sha256(new TextEncoder().encode(token)));

  // ✅ 삭제된 사용자 필터링 추가
  const result = await db
    .select({ user: userTable, session: sessionTable })
    .from(sessionTable)
    .innerJoin(userTable, eq(sessionTable.userId, userTable.id))
    .where(
      and(
        eq(sessionTable.id, sessionId),
        isNull(userTable.deletedAt) // ✅ 삭제되지 않은 사용자만
      )
    );

  if (result.length < 1) {
    return { session: null, user: null };
  }

  const { user, session } = result[0];

  // 세션 만료 확인
  if (Date.now() >= session.expiresAt.getTime()) {
    await db.delete(sessionTable).where(eq(sessionTable.id, session.id));
    return { session: null, user: null };
  }

  // 세션 만료 시간 갱신 (15일 이하 남은 경우)
  if (Date.now() >= session.expiresAt.getTime() - 1000 * 60 * 60 * 24 * 15) {
    session.expiresAt = new Date(Date.now() + 1000 * 60 * 60 * 24 * 30);
    await db
      .update(sessionTable)
      .set({
        expiresAt: session.expiresAt,
      })
      .where(eq(sessionTable.id, session.id));
  }

  return { session, user };
}

/**
 * 현재 요청의 쿠키에서 세션 토큰을 읽고, 해당 세션의 유효성을 검증한 뒤
 * 유효한 경우 세션과 사용자 정보를 반환합니다.
 *
 * Next.js 15에서는 `cookies()`가 비동기 함수이므로 `await`으로 호출해야 하며,
 * 캐싱된 결과를 반환하기 위해 `cache()`로 감쌉니다.
 *
 * @returns {Promise<SessionValidationResult>} 유효한 경우 세션과 사용자 객체, 없거나 만료된 경우 null 반환
 */
export const getCurrentSession = cache(
  async (): Promise<SessionValidationResult> => {
    const cookieStore = await cookies();
    const token = cookieStore.get('session')?.value ?? null;

    if (token === null) {
      return { session: null, user: null };
    }

    const result = await validateSessionToken(token);
    return result;
  }
);

/**
 * 세션 토큰을 'session' 쿠키에 저장합니다.
 *
 * 이 쿠키는 HTTP-only 속성이 설정되어 클라이언트 JavaScript에서는 접근할 수 없으며,
 * 보안을 위해 Secure, SameSite 등의 설정도 함께 적용됩니다.
 *
 * @param token - 저장할 세션 토큰 문자열
 * @param expiresAt - 쿠키 만료 일시 (Date 객체)
 */
export async function setSessionTokenCookie(
  token: string,
  expiresAt: Date
): Promise<void> {
  const cookieStore = await cookies(); // 요청 컨텍스트에서 쿠키 저장소 가져오기

  // 'session' 쿠키를 설정
  cookieStore.set('session', token, {
    httpOnly: true, // JS로 접근 불가, XSS 보호
    path: '/', // 루트 경로 전체에 적용
    secure: process.env.NODE_ENV === 'production', // HTTPS 환경에서만 전송
    sameSite: 'lax', // 기본적인 CSRF 보호
    expires: expiresAt, // 만료 시점 설정
  });
}

/**
 * 'session' 쿠키를 제거합니다.
 *
 * 쿠키를 제거하기 위해 동일한 설정을 유지한 채 maxAge: 0 또는 expires를 0으로 설정하여 무효화합니다.
 *
 * @returns {Promise<void>} 아무 것도 반환하지 않음
 */
export async function deleteSessionTokenCookie(): Promise<void> {
  const cookieStore = await cookies(); // 요청 컨텍스트에서 쿠키 저장소 가져오기

  // 'session' 쿠키를 무효화하여 삭제
  cookieStore.set('session', '', {
    httpOnly: true,
    path: '/', // 설정된 path가 삭제할 때도 동일해야 정확히 제거됨
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 0, // 즉시 만료되도록 설정
  });
}

/**
 * 주어진 세션 ID에 해당하는 세션을 데이터베이스에서 삭제합니다.
 *
 * 일반적으로 사용자가 로그아웃할 때 해당 세션을 무효화하는 데 사용됩니다.
 *
 * @param {string} sessionId - 삭제할 세션의 고유 식별자 (SHA-256 해시된 토큰 값)
 * @returns {Promise<void>} 반환값 없음
 *
 * @example
 * await invalidateSession(session.id);
 */
export async function invalidateSession(sessionId: string): Promise<void> {
  await db.delete(sessionTable).where(eq(sessionTable.id, sessionId));
}

/**
 * 특정 사용자 ID에 해당하는 모든 세션을 데이터베이스에서 삭제합니다.
 *
 * 보안상의 이유로 사용자의 모든 세션을 강제로 로그아웃시키고자 할 때 사용됩니다.
 * 예: 비밀번호 변경, 계정 탈취 대응 등
 *
 * @param {string} userId - 세션을 삭제할 대상 사용자 UUID
 * @returns {Promise<void>} 반환값 없음
 *
 * @example
 * await invalidateAllSessions(user.id);
 */
export async function invalidateAllSessions(userId: string): Promise<void> {
  await db.delete(sessionTable).where(eq(sessionTable.userId, userId));
}

export type SessionValidationResult =
  | { session: Session; user: User }
  | { session: null; user: null };
