import { db } from './db';
import { chatMessages, chatSessions, userLimits } from '@schema';
import { and, eq, gte, sql } from 'drizzle-orm';

/**
 * 기본 일일 채팅 한도 (DB에 설정이 없을 때 사용)
 */
const DEFAULT_DAILY_LIMIT = parseInt(process.env.DAILY_CHAT_LIMIT || '5');

/**
 * 오늘 날짜의 시작 시간 반환 (00:00:00)
 */
function getTodayStart(): Date {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return today;
}

/**
 * 사용자의 일일 한도 설정 조회
 * @param userId - 사용자 ID
 * @returns 사용자의 일일 한도
 */
export async function getUserDailyLimit(userId: string): Promise<number> {
  try {
    const result = await db
      .select({
        dailyChatLimit: userLimits.dailyChatLimit,
      })
      .from(userLimits)
      .where(eq(userLimits.userId, userId))
      .limit(1);

    // DB에 설정이 있으면 해당 값 사용, 없으면 기본값 사용
    return result[0]?.dailyChatLimit || DEFAULT_DAILY_LIMIT;
  } catch (error) {
    console.error('사용자 한도 조회 실패:', error);
    return DEFAULT_DAILY_LIMIT; // 에러 시 기본값 반환
  }
}

/**
 * 사용자의 오늘 메시지 수 조회
 * @param userId - 사용자 ID
 * @returns 오늘 보낸 user 메시지 수
 */
export async function getTodayMessageCount(userId: string): Promise<number> {
  try {
    const todayStart = getTodayStart();

    const result = await db
      .select({
        count: sql<number>`COUNT(*)`,
      })
      .from(chatMessages)
      .innerJoin(chatSessions, eq(chatMessages.sessionId, chatSessions.id))
      .where(
        and(
          eq(chatSessions.userId, userId),
          eq(chatMessages.role, 'user'), // user 메시지만 카운트
          gte(chatMessages.createdAt, todayStart)
        )
      );

    return Number(result[0]?.count || 0);
  } catch (error) {
    console.error('오늘 메시지 수 조회 실패:', error);
    return 0; // 에러 시 0 반환 (안전한 기본값)
  }
}

/**
 * 사용자의 일일 채팅 한도 확인
 * @param userId - 사용자 ID
 * @returns 한도 정보 객체
 */
export async function checkDailyLimit(userId: string): Promise<{
  canSend: boolean;
  used: number;
  limit: number;
  remaining: number;
}> {
  // 병렬로 한도와 사용량 조회
  const [limit, used] = await Promise.all([
    getUserDailyLimit(userId),
    getTodayMessageCount(userId),
  ]);

  const remaining = Math.max(0, limit - used);

  return {
    canSend: used < limit,
    used,
    limit,
    remaining,
  };
}

/**
 * 신규 사용자의 기본 한도 설정 생성
 * @param userId - 사용자 ID
 * @param limitType - 한도 타입 (기본값: 'standard')
 */
export async function createDefaultUserLimit(
  userId: string,
  limitType: 'standard' | 'premium' | 'vip' | 'custom' = 'standard'
): Promise<void> {
  try {
    // 한도 타입별 기본값 설정
    const limitByType = {
      standard: 5,
      premium: 20,
      vip: 99, // 실질적 무제한
      custom: DEFAULT_DAILY_LIMIT,
    };

    await db
      .insert(userLimits)
      .values({
        userId,
        dailyChatLimit: limitByType[limitType],
        limitType,
        createdAt: new Date(),
        updatedAt: new Date(),
      })
      .onConflictDoNothing(); // 이미 존재하면 무시

    console.log(
      `사용자 ${userId}의 기본 한도 설정 완료: ${limitByType[limitType]}회 (${limitType})`
    );
  } catch (error) {
    console.error('기본 한도 설정 생성 실패:', error);
    // 에러가 발생해도 앱이 중단되지 않도록 함
  }
}
