import { db } from './db';
import { userLimits } from '@schema';
import { eq } from 'drizzle-orm';

/**
 * 사용자 한도 업데이트
 * @param userId - 사용자 ID
 * @param newLimit - 새로운 한도
 * @param limitType - 한도 타입
 */
export async function updateUserLimit(
  userId: string,
  newLimit: number,
  limitType: 'standard' | 'premium' | 'vip' | 'custom' = 'custom'
): Promise<void> {
  try {
    const result = await db
      .update(userLimits)
      .set({
        dailyChatLimit: newLimit,
        limitType,
        updatedAt: new Date(),
      })
      .where(eq(userLimits.userId, userId))
      .returning({ userId: userLimits.userId });

    if (result.length === 0) {
      // 기존 설정이 없으면 새로 생성
      await db.insert(userLimits).values({
        userId,
        dailyChatLimit: newLimit,
        limitType,
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }

    console.log(
      `사용자 ${userId}의 한도가 ${newLimit}회로 변경됨 (${limitType})`
    );
  } catch (error) {
    console.error('사용자 한도 업데이트 실패:', error);
    throw error;
  }
}

/**
 * 여러 사용자에게 일괄 한도 적용
 * @param userIds - 사용자 ID 배열
 * @param limit - 적용할 한도
 * @param limitType - 한도 타입
 */
export async function bulkUpdateUserLimits(
  userIds: string[],
  limit: number,
  limitType: 'standard' | 'premium' | 'vip' | 'custom'
): Promise<void> {
  try {
    const values = userIds.map((userId) => ({
      userId,
      dailyChatLimit: limit,
      limitType,
      createdAt: new Date(),
      updatedAt: new Date(),
    }));

    await db
      .insert(userLimits)
      .values(values)
      .onConflictDoUpdate({
        target: [userLimits.userId],
        set: {
          dailyChatLimit: limit,
          limitType,
          updatedAt: new Date(),
        },
      });

    console.log(
      `${userIds.length}명의 사용자 한도를 ${limit}회로 일괄 변경 (${limitType})`
    );
  } catch (error) {
    console.error('일괄 한도 업데이트 실패:', error);
    throw error;
  }
}

/**
 * 사용자의 현재 한도 설정 조회
 * @param userId - 사용자 ID
 * @returns 한도 설정 정보
 */
export async function getUserLimitInfo(userId: string) {
  try {
    const result = await db
      .select()
      .from(userLimits)
      .where(eq(userLimits.userId, userId))
      .limit(1);

    return result[0] || null;
  } catch (error) {
    console.error('사용자 한도 정보 조회 실패:', error);
    return null;
  }
}
